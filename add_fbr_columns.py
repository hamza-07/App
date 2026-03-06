"""
One-time script to add FBR columns to existing SQLite database.
Run: python add_fbr_columns.py
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///hamza_enterprises.db')
# Convert sqlite:///hamza_enterprises.db to path
if DATABASE_URL.startswith('sqlite:///'):
    db_path = DATABASE_URL.replace('sqlite:///', '')
    if db_path == ':memory:':
        print("Cannot migrate in-memory database.")
        exit(1)
    # instance folder is often used by Flask
    if not os.path.isabs(db_path) and not os.path.exists(db_path):
        alt = os.path.join('instance', db_path)
        if os.path.exists(alt):
            db_path = alt
else:
    print("This script only supports SQLite.")
    exit(1)

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def get_columns(table):
    cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]

# Invoices: add FBR columns
invoice_cols = get_columns('invoices')
invoice_add = [
    ('invoice_time', 'VARCHAR(10)'),
    ('invoice_type', 'VARCHAR(50)'),
    ('payment_mode', 'VARCHAR(30)'),
    ('discount_amount', 'NUMERIC(10,2) DEFAULT 0'),
    ('payment_bank_name', 'VARCHAR(100)'),
    ('payment_account_no', 'VARCHAR(50)'),
    ('payment_transaction_id', 'VARCHAR(100)'),
    ('payment_due_date', 'DATE'),
]
for col_name, col_type in invoice_add:
    if col_name not in invoice_cols:
        try:
            cur.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            print(f"  + invoices.{col_name}")
        except sqlite3.OperationalError as e:
            print(f"  skip invoices.{col_name}: {e}")
        else:
            invoice_cols.append(col_name)

# Settings: add FBR columns
try:
    settings_cols = get_columns('settings')
except sqlite3.OperationalError:
    settings_cols = []
settings_add = [
    ('company_email', 'VARCHAR(100)'),
    ('business_type', 'VARCHAR(50)'),
]
for col_name, col_type in settings_add:
    if col_name not in settings_cols:
        try:
            cur.execute(f"ALTER TABLE settings ADD COLUMN {col_name} {col_type}")
            print(f"  + settings.{col_name}")
        except sqlite3.OperationalError as e:
            print(f"  skip settings.{col_name}: {e}")

# Quotation items: manual rate option
try:
    qi_cols = get_columns('quotation_items')
    if 'use_manual_rate' not in qi_cols:
        cur.execute("ALTER TABLE quotation_items ADD COLUMN use_manual_rate BOOLEAN DEFAULT 0")
        print("  + quotation_items.use_manual_rate")
except sqlite3.OperationalError as e:
    print(f"  skip quotation_items: {e}")

# Challan items: loss quantity
try:
    ci_cols = get_columns('challan_items')
    if 'loss_quantity' not in ci_cols:
        cur.execute("ALTER TABLE challan_items ADD COLUMN loss_quantity INTEGER DEFAULT 0")
        print("  + challan_items.loss_quantity")
except sqlite3.OperationalError as e:
    print(f"  skip challan_items: {e}")

conn.commit()
conn.close()
print("Done. FBR columns added.")
