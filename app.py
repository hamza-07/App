"""
Hamza Enterprises - Packaging Factory Management System
Flask Web Application for Quotation → Challan → Invoice Workflow
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///hamza_enterprises.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PDF_FOLDER'] = 'generated_pdfs'

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['PDF_FOLDER'], 'static/images']:
    os.makedirs(folder, exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Add custom Jinja2 filters
@app.template_filter('date')
def date_filter(s, fmt='%Y-%m-%d'):
    if s is None:
        return ''
    if isinstance(s, str):
        s = datetime.strptime(s, '%Y-%m-%d')
    return s.strftime(fmt)

# Import models and routes
from models import *
from routes import *


def ensure_database_columns():
    """Add missing columns to existing DB if missing (SQLite). Safe to run every startup."""
    if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
        return
    import sqlite3
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    path = uri.replace('sqlite:///', '')
    if path == ':memory:':
        return
    if not os.path.isabs(path) and not os.path.exists(path):
        alt = os.path.join(app.instance_path, path)
        if os.path.exists(alt):
            path = alt
    if not os.path.exists(path):
        return
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    def cols(table):
        cur.execute(f"PRAGMA table_info({table})")
        return [r[1] for r in cur.fetchall()]

    # Invoice Columns
    for col_name, col_type in [
        ('invoice_time', 'VARCHAR(10)'), ('invoice_type', 'VARCHAR(50)'),
        ('payment_mode', 'VARCHAR(30)'), ('discount_amount', 'NUMERIC(10,2) DEFAULT 0'),
        ('payment_bank_name', 'VARCHAR(100)'), ('payment_account_no', 'VARCHAR(50)'),
        ('payment_transaction_id', 'VARCHAR(100)'), ('payment_due_date', 'DATE'),
    ]:
        if col_name not in cols('invoices'):
            try:
                cur.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass
    
    # Settings Columns
    settings_cols = [
        ('company_email', 'VARCHAR(100)'), 
        ('business_type', 'VARCHAR(50)'),
        ('header_image', 'VARCHAR(200)'),
        ('footer_image', 'VARCHAR(200)'),
        ('signature_image', 'VARCHAR(200)'),
        ('stamp_image', 'VARCHAR(200)'),
        ('terms_duration', 'VARCHAR(200)'),
        ('terms_validity', 'VARCHAR(200)'),
        ('terms_payment', 'VARCHAR(200)'),
        ('google_drive_connected', 'BOOLEAN DEFAULT 0'),
        ('fbr_pos_id', 'VARCHAR(50)'),
        ('fbr_auth_token', 'VARCHAR(500)')
    ]
    
    for col_name, col_type in settings_cols:
        if col_name not in cols('settings'):
            try:
                cur.execute(f"ALTER TABLE settings ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass

    if 'use_manual_rate' not in cols('quotation_items'):
        try:
            cur.execute("ALTER TABLE quotation_items ADD COLUMN use_manual_rate BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
    try:
        challan_cols = cols('challan_items')
        if 'loss_quantity' not in challan_cols:
            cur.execute("ALTER TABLE challan_items ADD COLUMN loss_quantity INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_database_columns()
    app.run(debug=True, host='0.0.0.0', port=5000)
