"""Versioned application-owned policy addendum; draft wording, never legal approval."""
import hashlib,json
VERSION='masked-replay-terms-draft-2026-11-07-v1'
TITLE='Optional Masked Session Replay'
TERMS=[
 'Eligible masked session replay helps TeleTena investigate technical problems and improve navigation. It captures page layout and safe interactions such as navigation, scrolling and button use, with displayed and entered text masked.',
 'Passwords, verification codes, authentication tokens, medical history, clinical notes, request descriptions, messages, identity documents, payment receipts, private file links and consultation audio or video are excluded. Uploaded images and document previews are blocked.',
 'Visiting TeleTena, dismissing a notice or accepting an earlier Terms version does not enable replay. Accepting these Terms alone does not select optional replay. Guests currently have no Terms acceptance step and are not recorded.',
 'When replay becomes available, signed-in users can manage their separate optional choice in Help & Tours under Journey Collection Preferences. Turn it off there without losing access to TeleTena. Signing in does not carry a guest choice into an account; signing out stops that account’s capture.',
 'See the Privacy Notice section on replay providers and retention. Production replay remains disabled while this draft wording, consent model and technical checks are reviewed.'
]
PRIVACY_TITLE='Replay Providers and Retention'
PRIVACY=[
 'PostHog is the selected provider for eligible masked replay. Accepted recordings follow the selected project’s configured retention and plan; the operator must verify those settings before activation. TeleTena does not promise a verified provider retention period here.',
 'The proposed private TeleTena archive is separate from PostHog retention. Its design is rolling deletion 90 days from original capture, not from export or a calendar-quarter boundary. Production archive availability remains conditional on complete export, independent playback, storage, access and deletion verification.',
 'Turning replay off stops future capture and discards unsent buffers. Previously transmitted recordings remain subject to the applicable deletion and retention process; a previously viewed image cannot be recalled. Raw replay expiry does not erase clinical, financial, support or audit records under their separate policies.',
 'These sections are review drafts. They do not establish legal approval, approved production policy or authorization to collect excluded sensitive information.'
]

def version(base,kind):
    return kind+'-review-'+hashlib.sha256((base+'\n'+json.dumps(public(),ensure_ascii=False,sort_keys=True)).encode()).hexdigest()[:40]

def public():
    return {'version':VERSION,'review_only':True,'terms_title':TITLE,'terms':TERMS,'privacy_title':PRIVACY_TITLE,'privacy':PRIVACY,'guest_acceptance_available':False,'guest_replay_available':False}
