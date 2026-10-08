"""Backfill missing refund activity only from exact subledger evidence."""
import uuid

import frappe


def backfill_refund_activity(patient=None):
    earnings = frappe.db.sql('''SELECT e.id earning_id,e.patient,e.clinician,e.net_minor,
            j.id journal_id,j.event_type,j.created journal_created
        FROM tt_earning e
        JOIN tt_journal j ON j.event_ref=CONCAT('earning-refund:',e.id)
        WHERE e.state='Refunded' AND (%s IS NULL OR e.patient=%s)
        ORDER BY e.id''', (patient, patient), as_dict=True)
    inserted = 0
    for earning in earnings:
        if earning.event_type != 'EarningRefunded':
            frappe.throw('Refund activity does not match its financial journal; review required',
                         frappe.ValidationError)
        amount = int(earning.net_minor)
        patient_account = 'patient:' + earning.patient + ':available'
        clinician_account = 'clinician:' + earning.clinician + ':pending'
        patient_credits = frappe.db.sql('''SELECT COALESCE(SUM(credit_minor),0) FROM tt_journal_line
            WHERE journal_id=%s AND account_id=%s''', (earning.journal_id, patient_account))[0][0]
        clinician_debits = frappe.db.sql('''SELECT COALESCE(SUM(debit_minor),0) FROM tt_journal_line
            WHERE journal_id=%s AND account_id=%s''', (earning.journal_id, clinician_account))[0][0]
        if int(patient_credits) != amount or int(clinician_debits) != amount:
            frappe.throw('Refund journal does not match its earning; review required',
                         frappe.ValidationError)
        reference = 'earning-refund:' + earning.earning_id
        existing = frappe.db.sql('''SELECT patient,kind,amount FROM tt_ledger WHERE reference=%s''',
                                  (reference,), as_dict=True)
        if existing:
            event = existing[0]
            if (event.patient != earning.patient or event.kind != 'Refund' or
                    int(event.amount) != amount):
                frappe.throw('Existing refund activity conflicts with its journal; review required',
                             frappe.ValidationError)
            continue
        frappe.db.sql('''INSERT INTO tt_ledger (id,patient,kind,amount,reference,created)
            VALUES (%s,%s,'Refund',%s,%s,%s)''',
            (str(uuid.uuid4()), earning.patient, amount, reference, earning.journal_created))
        inserted += 1
    return inserted


def execute():
    inserted = backfill_refund_activity()
    from tele_tena.patches.v1_13_financial_reconciliation_audit import audit_wallet
    wallets = frappe.db.sql('SELECT patient FROM tt_wallet ORDER BY patient', as_dict=True)
    for wallet in wallets:
        audit_wallet(wallet.patient)
    return {'refund_events_added': inserted, 'wallets_reaudited': len(wallets)}
