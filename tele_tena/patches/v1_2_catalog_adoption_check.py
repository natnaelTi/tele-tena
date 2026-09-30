"""Complete catalog adoption if an early draft patch was already recorded."""
def execute():
    from tele_tena.patches.v1_1_native_catalog import execute as copy_catalog
    copy_catalog()
