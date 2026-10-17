"""Allowlisted public professional facts. No patient,account or evidence projection."""
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import frappe
from tele_tena.api.journey import _approved_offerings,rows,fail

PUBLIC_FIELDS=('id','clinician_id','display_name','label','description','service_category',
               'participant_structure','price','minutes','care_languages','schedule_timezone','consultation_format')


def availability(offering):
    """Authoritative capacity summary; never return occupied appointments."""
    from tele_tena.api import scheduling,open_requests
    schedule=scheduling._schedule_for(offering)
    if not schedule or schedule.status!='Published':return {'state':'unpublished','available_now':False,'has_booking_times':False}
    offer=rows('SELECT * FROM tt_offering WHERE id=%s AND active=1',(offering,))
    if not offer:return {'state':'unpublished','available_now':False,'has_booking_times':False}
    offer=offer[0];instant=datetime.now(timezone.utc).replace(tzinfo=None)
    presence=rows('SELECT ready,expires_at FROM tt_clinician_request_presence WHERE clinician=%s',(offer.clinician,))
    live=bool(presence and presence[0].ready and presence[0].expires_at>instant)
    start=scheduling.immediate_capacity(offering) if live else None
    immediate=bool(start)
    # A summary of genuinely generated slots,not a booked/busy time feed.
    day=datetime.now(ZoneInfo(schedule.timezone)).date();next_time=None
    horizon=min(int(schedule.horizon_days),366)
    booked=rows("SELECT start,end,buffer_before,buffer_after FROM tt_appointment WHERE clinician=%s AND state IN ('Booked','PendingConfirmation') AND end>%s AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))",(offer.clinician,instant))
    for offset in range(horizon+1):
        slots=scheduling._slots_for_day(schedule,offer,day+timedelta(days=offset),booked)
        if slots:next_time=slots[0][0];break
    return {'state':'available_now' if start else 'capacity_paused' if live and not start else 'appointment_only' if next_time else 'no_openings',
            'available_now':bool(start),'has_booking_times':bool(next_time),'timezone':schedule.timezone,
            'next_available_at':next_time.isoformat()+'Z' if next_time else None,
            'checked_at':instant.isoformat()+'Z'}


def _items():
    from tele_tena.api.profile_photos import public_photo
    result=[]
    for offer in _approved_offerings():
        item={key:offer.get(key) for key in PUBLIC_FIELDS}
        # Public photo is separately checked against publication/current approval.
        photo=offer.get('photo_url')
        item['photo_url']=photo.replace('tele_tena.api.profile_photos.download','tele_tena.api.directory.photo') if photo else None
        item['availability']=availability(offer.id)
        result.append(item)
    return result


@frappe.whitelist(allow_guest=True,methods=['GET'])
def offerings(service='',language='',consultation_format='',availability_filter='',offering=''):
    for value in (service,language,consultation_format,availability_filter,offering):
        if not isinstance(value,str) or len(value)>140:fail('Invalid directory filter')
    if language not in ('','en','am','om') or consultation_format not in ('','audio','video') or availability_filter not in ('','now','appointment'):
        fail('Choose supported filters')
    items=_items();categories=sorted({item['service_category'] for item in items})
    items=[item for item in items if (not service or item['service_category']==service)
           and (not language or language in item['care_languages'])
           and (not consultation_format or item['consultation_format']==consultation_format)
           and (not offering or item['id']==offering)
           and (not availability_filter or (item['availability']['available_now'] if availability_filter=='now' else item['availability']['has_booking_times'] and not item['availability']['available_now']))]
    return {'items':items,'categories':categories,'checked_at':datetime.now(timezone.utc).isoformat(),'poll_after_seconds':30}


@frappe.whitelist(allow_guest=True,methods=['GET'])
def clinician(clinician_id):
    from tele_tena.api.open_requests import _public_clinician
    profile=_public_clinician(clinician_id)
    allowed=[item for item in _items() if item['clinician_id']==clinician_id]
    if not allowed:fail('Clinician unavailable')
    # Deliberate outer and inner allowlists; never serialize the private profile row.
    return {'display_name':profile['display_name'],'introduction':profile['introduction'],
            'approval_meaning':profile['approval_meaning'],'trust_indicators':profile['trust_indicators'],
            'photo_url':allowed[0]['photo_url'],
            'services':[{'offering':item['id'],**{key:item[key] for key in ('label','description','service_category','price','minutes','consultation_format','care_languages','availability')}} for item in allowed]}


@frappe.whitelist(allow_guest=True,methods=['GET'])
def photo(id):
    if not isinstance(id,str) or len(id)!=36:frappe.throw('Photo unavailable',frappe.PermissionError)
    from werkzeug.wrappers import Response
    eligible=_approved_offerings()
    expected='/api/method/tele_tena.api.profile_photos.download?id='+id
    if not any(item.photo_url==expected for item in eligible):frappe.throw('Photo unavailable',frappe.PermissionError)
    found=rows('SELECT content FROM tt_profile_photo WHERE id=%s AND published=1',(id,))
    if not found:frappe.throw('Photo unavailable',frappe.PermissionError)
    return Response(bytes(found[0].content),mimetype='image/jpeg',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
