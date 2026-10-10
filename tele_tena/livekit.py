"""Backend-only LiveKit configuration, participant tokens and room closure."""
import asyncio
import json
import os
import re
import stat
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import frappe


def _configuration_error(message):
    # Return a safe actionable category, never the credential values or path.
    frappe.local.response['tele_tena_error'] = 'consultation_service_unconfigured'
    frappe.throw(message, frappe.ValidationError)


def _credentials():
    path = Path(frappe.get_site_path('private', 'tele_tena_livekit.json'))
    if path.is_symlink() or not path.is_file():
        _configuration_error('LiveKit is not configured on this site')
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        _configuration_error('LiveKit credential file must have mode 600')
    try:
        values = json.loads(path.read_text())
        url, key, secret = values['url'], values['api_key'], values['api_secret']
    except (OSError, ValueError, KeyError, TypeError):
        _configuration_error('LiveKit configuration is invalid')
    parsed = urlsplit(url)
    local = parsed.hostname in ('localhost', '127.0.0.1', '::1')
    if parsed.scheme != 'wss' and not (local and parsed.scheme == 'ws'):
        _configuration_error('LiveKit URL must use wss (ws is allowed for loopback development)')
    if not parsed.netloc or parsed.username or parsed.password or not re.fullmatch(r'[A-Za-z0-9_-]{3,128}', key) or len(secret) < 16:
        _configuration_error('LiveKit configuration is invalid')
    return url, key, secret


def _api_url(url):
    return 'https://' + url[6:] if url.startswith('wss://') else 'http://' + url[5:]


def _token_ttl():
    value = frappe.conf.get('tele_tena_livekit_token_seconds', 300)
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 300
    return max(60, min(600, value))


def participant_token(room_name, identity, audio_only=False):
    """Issue minimal grants. Callers must have authorized the appointment first."""
    _, key, secret = _credentials()
    from livekit import api

    sources = ['microphone'] if audio_only else ['microphone', 'camera']
    return (api.AccessToken(key, secret)
            .with_identity(identity)
            .with_ttl(timedelta(seconds=_token_ttl()))
            .with_grants(api.VideoGrants(
                room_join=True, room=room_name, room_create=False, room_list=False,
                room_admin=False, room_record=False, can_publish=True,
                can_publish_sources=sources, can_subscribe=True,
                can_publish_data=False, can_update_own_metadata=False,
                ingress_admin=False, hidden=False, recorder=False, agent=False,
            )).to_jwt())


def close_room(room_name, identities=()):
    """On LiveKit Cloud revoke both aliases (including departed users), then delete."""
    import livekit.api
    url, key, secret = _credentials()
    cloud = (urlsplit(url).hostname or '').endswith('.livekit.cloud')

    async def delete():
        client = livekit.api.LiveKitAPI(_api_url(url), key, secret)
        try:
            failures = []
            if cloud:
                # Use a future cutoff to cover tokens refreshed between End's
                # commit and this provider call. It is comfortably inside the
                # Cloud API's documented 60-second acceptance window.
                for identity in identities:
                    cutoff = int(time.time()) + 30
                    try:
                        await client.room.remove_participant(livekit.api.RoomParticipantIdentity(
                            room=room_name, identity=identity, revoke_token_ts=cutoff))
                    except Exception as error:
                        failures.append(error)
            await client.room.delete_room(livekit.api.DeleteRoomRequest(room=room_name))
            if failures:
                raise failures[0]
        finally:
            await client.aclose()

    asyncio.run(delete())
