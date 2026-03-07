"""
Hamza Enterprises - Packaging Factory Management System
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Fix DATABASE_URL: SQLAlchemy requires postgresql:// not postgres://
_db_url = os.environ.get('DATABASE_URL', 'sqlite:////tmp/hamza_enterprises.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Folders: always use /tmp on Vercel (only writable location) ───────────────
_IS_VERCEL = os.environ.get('VERCEL', False)
_BASE_TMP  = '/tmp' if _IS_VERCEL else os.path.dirname(__file__)

app.config['UPLOAD_FOLDER']  = os.path.join(_BASE_TMP, 'uploads')
app.config['PDF_FOLDER']     = os.path.join(_BASE_TMP, 'generated_pdfs')

for folder in [app.config['UPLOAD_FOLDER'], app.config['PDF_FOLDER']]:
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        pass

# ── Extensions ────────────────────────────────────────────────────────────────
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ── Jinja2 filters ────────────────────────────────────────────────────────────
@app.template_filter('date')
def date_filter(s, fmt='%Y-%m-%d'):
    if s is None:
        return ''
    if isinstance(s, str):
        s = datetime.strptime(s, '%Y-%m-%d')
    return s.strftime(fmt)

# ── Models & Routes ───────────────────────────────────────────────────────────
from models import *
from routes import *

# ── DB Init ───────────────────────────────────────────────────────────────────
def init_db():
    """Safe DB init — wrapped so import never crashes Vercel cold start."""
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"[DB INIT WARNING] {e}")

# Only auto-init in local dev — on Vercel, call via CLI migration instead
if not _IS_VERCEL:
    init_db()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)  