"""Rollback-only MariaDB regression: fixture cleanup never repairs foreign data."""
import importlib.util
import os
import secrets
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
assert os.environ.get('TELE_TENA_TEST_SITE') == 'tele-tena-pr12-fresh.localhost'
spec = importlib.util.spec_from_file_location('cleanup_regression_fixtures', APP / 'tests/integration.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.connect()
try:
    from tele_tena import accounting
    prefix = 'cleanup-only-' + secrets.token_hex(12)
    owned = [f'patient:{prefix}-owned-{index}:available' for index in (1, 2)]
    counterparts = [f'patient:{prefix}-counterpart:available', f'patient:{prefix}-debit:cash_clearing']
    outsider = f'patient:{prefix}-unrelated:available'
    for account, side, opening in [(owned[0], 'C', 0), (owned[1], 'C', 0),
                                   (counterparts[0], 'C', 900), (counterparts[1], 'D', 900),
                                   (outsider, 'C', 777)]:
        _, owner, bucket = account.split(':', 2)
        m.frappe.db.sql('''INSERT INTO tt_financial_account
            (id,owner,bucket,normal_side,balance_minor) VALUES (%s,%s,%s,%s,%s)''',
            (account, owner, bucket, side, opening))
    # Intentional unmatched offsets exist only inside this rollback transaction.
    # The old global recomputation would silently erase 900/900/777 here.
    for index, counterpart in enumerate(counterparts):
        accounting.post(prefix + str(index), 'CleanupTest', prefix + str(index),
                        [(counterpart, 100, 0), (owned[index], 0, 100)])
    m.remove_owned_financial_fixtures(owned)
    for _ in range(2):
        rows = m.frappe.db.sql('SELECT id,balance_minor FROM tt_financial_account WHERE id IN %s',
                              (tuple(counterparts + [outsider]),), as_dict=True)
        assert {row.id: int(row.balance_minor) for row in rows} == {
            counterparts[0]: 900, counterparts[1]: 900, outsider: 777}
        assert not m.frappe.db.sql('SELECT id FROM tt_financial_account WHERE id IN %s', (tuple(owned),))
        assert not m.frappe.db.sql('SELECT id FROM tt_journal WHERE event_ref IN %s',
                                 ((prefix + '0', prefix + '1'),))
        m.remove_owned_financial_fixtures(owned)
    print('PASS: debit/credit counterpart offsets and unrelated owner preserved; cleanup retry safe; rollback-only.')
finally:
    m.frappe.db.rollback()
    m.frappe.destroy()
