"""Restore invoices, payments, and meter to the demo fixtures."""

import engine

if __name__ == "__main__":
    engine.reset_data()
    print("Demo data restored from fixtures/.")
