"""Adopt/create baseline command tables; existing records are never rewritten."""
def execute():
    from tele_tena.schema import create_tables
    create_tables()
