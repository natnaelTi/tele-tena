"""Import post-snapshot legacy wallet events into the demo subledger once.

The wallet and append-only simulation log remain unchanged. This patch only
adds balanced, traceable journals for known events that landed after a wallet's
v1.7 opening snapshot. Unknown event kinds fail the migration closed.
"""
import frappe


def reconcile_wallet_events(patient):
    from tele_tena.accounting import account_id, post

    opening = frappe.db.sql('SELECT created FROM tt_journal WHERE event_ref=%s',
                            ('opening:' + patient,), as_dict=True)
    params = [patient]
    after = ''
    if opening:
        after = ' AND created>%s'
        params.append(opening[0].created)
    events = frappe.db.sql('''SELECT id,kind,amount,reference,created FROM tt_ledger
        WHERE patient=%s''' + after + ' ORDER BY created,id', params, as_dict=True)
    imported = 0
    for event in events:
        already_posted = frappe.db.sql('SELECT id FROM tt_journal WHERE event_ref=%s',
                                       (event.reference,))
        if already_posted:
            continue
        amount = int(event.amount)
        available = account_id('patient', patient, 'available')
        reserved = account_id('patient', patient, 'reserved')
        clearing = account_id('demo', '', 'cash_clearing')
        if event.kind == 'Deposit':
            lines = [(clearing, amount, 0), (available, 0, amount)]
        elif event.kind == 'Reservation':
            lines = [(available, amount, 0), (reserved, 0, amount)]
        elif event.kind == 'Release':
            lines = [(reserved, amount, 0), (available, 0, amount)]
        else:
            frappe.throw('Unknown legacy financial event; migration requires review',
                         frappe.ValidationError)
        post(event.reference, 'LegacyEventImported', 'legacy-import:' + event.id,
             lines, {'source': 'tt_ledger', 'legacy_event_id': event.id,
                     'legacy_kind': event.kind})
        imported += 1
    return imported


def execute():
    wallets = frappe.db.sql('SELECT patient FROM tt_wallet ORDER BY patient', as_dict=True)
    for wallet in wallets:
        reconcile_wallet_events(wallet.patient)
