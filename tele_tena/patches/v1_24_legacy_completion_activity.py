"""Backfill provable missing completion activity and re-audit wallet projections.

This does not change wallets, appointments, earnings, or journals. A log row is
added only when the immutable completion journal, its patient reserved debit,
and the matching earning all agree exactly. Ambiguous legacy discrepancies stay
visible for authorized review.
"""
import uuid

import frappe


def backfill_completion_activity(patient=None):
    rows = frappe.db.sql('''SELECT e.id earning_id,e.appointment,e.patient,e.gross_minor,
            j.id journal_id,j.event_type,j.created journal_created
        FROM tt_earning e
        JOIN tt_journal j ON j.event_ref=CONCAT('completion:',e.appointment)
        WHERE e.completed_at IS NOT NULL AND (%s IS NULL OR e.patient=%s)
        ORDER BY e.appointment''', (patient, patient), as_dict=True)
    inserted = 0
    for row in rows:
        if row.event_type != 'ConsultationFinalized':
            frappe.throw('Completion activity does not match its financial journal; review required',
                         frappe.ValidationError)
        reserved_account = 'patient:' + row.patient + ':reserved'
        debits = frappe.db.sql('''SELECT COALESCE(SUM(debit_minor),0) FROM tt_journal_line
            WHERE journal_id=%s AND account_id=%s''', (row.journal_id, reserved_account))[0][0]
        if int(debits) != int(row.gross_minor):
            frappe.throw('Completion journal amount does not match its earning; review required',
                         frappe.ValidationError)
        reference = 'completion:' + row.appointment
        existing = frappe.db.sql('''SELECT patient,kind,amount FROM tt_ledger WHERE reference=%s''',
                                  (reference,), as_dict=True)
        if existing:
            event = existing[0]
            if (event.patient != row.patient or event.kind != 'Consumption' or
                    int(event.amount) != int(row.gross_minor)):
                frappe.throw('Existing completion activity conflicts with its journal; review required',
                             frappe.ValidationError)
            continue
        frappe.db.sql('''INSERT INTO tt_ledger (id,patient,kind,amount,reference,created)
            VALUES (%s,%s,'Consumption',%s,%s,%s)''',
            (str(uuid.uuid4()), row.patient, int(row.gross_minor), reference, row.journal_created))
        inserted += 1
    return inserted


def execute():
    inserted = backfill_completion_activity()
    from tele_tena.patches.v1_13_financial_reconciliation_audit import audit_wallet
    wallets = frappe.db.sql('SELECT patient FROM tt_wallet ORDER BY patient', as_dict=True)
    for wallet in wallets:
        audit_wallet(wallet.patient)
    return {'completion_events_added': inserted, 'wallets_reaudited': len(wallets)}
