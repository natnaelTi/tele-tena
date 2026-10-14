"""No public file paths, EXIF, generic document access or patient photo sharing."""
import base64
import io
import uuid
import warnings

import frappe
from PIL import Image, ImageOps, UnidentifiedImageError
from tele_tena.api.journey import actor, command, fail, query, rows

MAX_BYTES = 3 * 1024 * 1024


def photo_url(photo_id):
    return '/api/method/tele_tena.api.profile_photos.download?id=' + photo_id


def _table_ready():
    # The app checkout can be shared with a site awaiting its own migration.
    # Keep existing session/discovery working; never migrate that other site here.
    return bool(frappe.db.sql("SHOW TABLES LIKE 'tt_profile_photo'"))


def owner_photo(user):
    if not _table_ready():
        return {'url': None, 'published': False}
    found = rows('SELECT id,published FROM tt_profile_photo WHERE user=%s', (user,))
    return {'url': photo_url(found[0].id), 'published': bool(found[0].published)} if found else {'url': None, 'published': False}


def public_photo(user):
    if not _table_ready():
        return None
    found = rows('SELECT id FROM tt_profile_photo WHERE user=%s AND published=1', (user,))
    return photo_url(found[0].id) if found else None


def _normalize(filename, content_base64):
    if not isinstance(filename, str) or not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        fail('Choose a JPEG, PNG or WebP image.', 'photo_invalid')
    if not isinstance(content_base64, str) or len(content_base64) > (MAX_BYTES + 2) // 3 * 4:
        fail('Choose an image no larger than 3 MB.', 'photo_invalid')
    try:
        content = base64.b64decode(content_base64, validate=True)
        if not content or len(content) > MAX_BYTES:
            raise ValueError()
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError()
                if min(image.size) < 32 or max(image.size) > 4096 or image.width * image.height > 16_000_000:
                    raise ValueError()
                image.load()
                image = ImageOps.exif_transpose(image).convert('RGB')
                image = ImageOps.fit(image, (512, 512), method=Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=88)
                return output.getvalue()
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        fail('Choose a valid, non-animated JPEG, PNG or WebP image up to 3 MB and 4096 pixels.', 'photo_invalid')


def can_publish(user):
    return 'Tele Tena Clinician' in frappe.get_roles(user) or 'Tele Tena Applicant' in frappe.get_roles(user)


@query()
def status():
    user = actor()
    return {**owner_photo(user), 'can_publish': can_publish(user)}


@command
def upload(filename, content_base64, published=0):
    user = actor()
    if str(published) not in ('0', '1', 'False', 'True'):
        fail('Choose a photo visibility.', 'photo_invalid')
    publish = str(published) in ('1', 'True')
    if publish and not can_publish(user):
        frappe.throw('Public photo unavailable', frappe.PermissionError)
    content = _normalize(filename, content_base64)
    # Serialize replace/remove for this owner. Never accept a caller-supplied owner.
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE', (user,))
    frappe.db.sql('''INSERT INTO tt_profile_photo (user,id,content,published,modified)
        VALUES (%s,%s,FROM_BASE64(%s),%s,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE
        id=VALUES(id),content=VALUES(content),published=VALUES(published),modified=VALUES(modified)''',
        (user, str(uuid.uuid4()), base64.b64encode(content).decode("ascii"), int(publish)))
    return owner_photo(user)


@command
def remove():
    user = actor()
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE', (user,))
    frappe.db.sql('DELETE FROM tt_profile_photo WHERE user=%s', (user,))
    return owner_photo(user)


@command
def set_visibility(published):
    user = actor()
    if str(published) not in ('0', '1'):
        fail('Choose a photo visibility.', 'photo_invalid')
    if str(published) == '1' and not can_publish(user):
        frappe.throw('Public photo unavailable', frappe.PermissionError)
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE', (user,))
    frappe.db.sql('UPDATE tt_profile_photo SET published=%s,modified=UTC_TIMESTAMP(6) WHERE user=%s', (int(published), user))
    return owner_photo(user)


@query()
def download(id):
    user = actor()
    found = rows('SELECT user,content,published FROM tt_profile_photo WHERE id=%s', (id,))
    if not found:
        frappe.throw('Photo unavailable', frappe.PermissionError)
    photo = found[0]
    if user != photo.user:
        if not photo.published or 'Tele Tena Patient' not in frappe.get_roles(user):
            frappe.throw('Photo unavailable', frappe.PermissionError)
        from tele_tena.api.journey import discover
        public_id = frappe.db.sql('SELECT public_id FROM tt_profile WHERE user=%s', (photo.user,))
        if not public_id or not any(item.clinician_id == public_id[0][0] for item in discover()):
            frappe.throw('Photo unavailable', frappe.PermissionError)
    from werkzeug.wrappers import Response
    return Response(bytes(photo.content), mimetype='image/jpeg', headers={
        'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff',
        'Content-Disposition': 'inline; filename="profile.jpg"'})
