"""
Database Models for Hamza Enterprises Factory Management System
"""

from app import db
from datetime import datetime
from sqlalchemy import Numeric

class Customer(db.Model):
    """Customer/Party Management"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    customer_name = db.Column(db.String(200))
    phone = db.Column(db.String(20), nullable=False)
    cnic = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    billing_address = db.Column(db.Text)  # Separate billing address
    shipping_address = db.Column(db.Text)  # Separate shipping address
    strn = db.Column(db.String(50))  # Sales Tax Registration Number
    ntn = db.Column(db.String(50))  # National Tax Number
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quotations = db.relationship('Quotation', backref='customer', lazy=True, cascade='all, delete-orphan')
    challans = db.relationship('Challan', backref='customer', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'customer_name': self.customer_name,
            'phone': self.phone,
            'cnic': self.cnic,
            'email': self.email,
            'address': self.address,
            'billing_address': self.billing_address,
            'shipping_address': self.shipping_address,
            'strn': self.strn,
            'ntn': self.ntn
        }

class PaperGrade(db.Model):
    """Paper Quality/Grade Settings"""
    __tablename__ = 'paper_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Kraft 125g", "Fluting 115g"
    gsm = db.Column(db.Numeric(10, 2), nullable=False)  # Grams per square meter
    rate_per_kg = db.Column(db.Numeric(10, 2), nullable=False)  # PKR per kg
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RollGrade(db.Model):
    """Roll (Corrugation) Quality Settings"""
    __tablename__ = 'roll_grades'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Standard Roll", "Premium Roll"
    rate_per_roll = db.Column(db.Numeric(10, 2), nullable=False)  # PKR per roll (2400 inches)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Settings(db.Model):
    """System Settings - FBR seller info"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    silicate_rate = db.Column(db.Numeric(10, 4), default=0.0035)
    labour_rate = db.Column(db.Numeric(10, 2), default=0)
    cartage_rate = db.Column(db.Numeric(10, 2), default=0)
    profit_margin_percent = db.Column(db.Numeric(5, 2), default=15.00)
    wastage_percent = db.Column(db.Numeric(5, 2), default=3.00)
    flute_factor = db.Column(db.Numeric(5, 2), default=1.4)
    company_name = db.Column(db.String(200), default='HAMZA HUSSAIN ENTERPRISES PAKISTAN (PVT) LTD')
    company_address = db.Column(db.Text)
    company_phone = db.Column(db.String(20))
    company_strn = db.Column(db.String(50))
    company_ntn = db.Column(db.String(50))
    company_email = db.Column(db.String(100))
    business_type = db.Column(db.String(50), default='Manufacturer')  # Manufacturer/Retailer/Wholesaler
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class Quotation(db.Model):
    """Quotation Management"""
    __tablename__ = 'quotations'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    quotation_date = db.Column(db.Date, default=datetime.utcnow)
    validity_days = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default='Draft')  # Draft, Sent, Approved, Rejected, Expired, Partially Delivered, Closed
    terms_conditions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('QuotationItem', backref='quotation', lazy=True, cascade='all, delete-orphan')
    challans = db.relationship('Challan', backref='quotation', lazy=True)
    
    def get_total_quantity(self):
        return sum(item.quantity for item in self.items)
    
    def get_delivered_quantity(self):
        total = 0
        for challan in self.challans:
            for item in challan.items:
                total += item.total_quantity
        return total
    
    def get_pending_quantity(self):
        return self.get_total_quantity() - self.get_delivered_quantity()

class QuotationItem(db.Model):
    """Quotation Line Items"""
    __tablename__ = 'quotation_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    length = db.Column(db.Numeric(10, 2), nullable=False)  # in inches
    width = db.Column(db.Numeric(10, 2), nullable=False)
    height = db.Column(db.Numeric(10, 2), nullable=False)
    ply = db.Column(db.Integer, nullable=False)  # 3, 5, or 7
    printing = db.Column(db.Boolean, default=False)
    printing_sides = db.Column(db.Integer, default=0)  # Number of sides with printing
    pcs = db.Column(db.Integer, default=1)  # 1 or 2 pieces
    joint_type = db.Column(db.String(20), default='Glue')  # Pin or Glue
    quantity = db.Column(db.Integer, nullable=False)
    
    # Material selections
    top_paper_id = db.Column(db.Integer, db.ForeignKey('paper_grades.id'))
    middle_paper_id = db.Column(db.Integer, db.ForeignKey('paper_grades.id'), nullable=True)
    bottom_paper_id = db.Column(db.Integer, db.ForeignKey('paper_grades.id'))
    flute1_roll_id = db.Column(db.Integer, db.ForeignKey('roll_grades.id'))
    flute2_roll_id = db.Column(db.Integer, db.ForeignKey('roll_grades.id'), nullable=True)
    flute3_roll_id = db.Column(db.Integer, db.ForeignKey('roll_grades.id'), nullable=True)
    
    # Calculated rates
    unit_rate = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Additional costs
    printing_cost = db.Column(db.Numeric(10, 2), default=0)
    labour_cost = db.Column(db.Numeric(10, 2), default=0)
    cartage_cost = db.Column(db.Numeric(10, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Challan(db.Model):
    """Delivery Challan"""
    __tablename__ = 'challans'
    
    id = db.Column(db.Integer, primary_key=True)
    challan_number = db.Column(db.String(50), unique=True, nullable=False)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    challan_date = db.Column(db.Date, default=datetime.utcnow)
    po_number = db.Column(db.String(100))  # Purchase Order Number
    driver_name = db.Column(db.String(100))
    vehicle_no = db.Column(db.String(50))
    driver_contact = db.Column(db.String(20))
    is_invoiced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('ChallanItem', backref='challan', lazy=True, cascade='all, delete-orphan')
    invoice_items = db.relationship('InvoiceItem', backref='challan', lazy=True)

class ChallanItem(db.Model):
    """Challan Line Items"""
    __tablename__ = 'challan_items'
    
    id = db.Column(db.Integer, primary_key=True)
    challan_id = db.Column(db.Integer, db.ForeignKey('challans.id'), nullable=False)
    quotation_item_id = db.Column(db.Integer, db.ForeignKey('quotation_items.id'), nullable=True)
    description = db.Column(db.String(500), nullable=False)
    boxes = db.Column(db.Integer, nullable=False)
    bundles = db.Column(db.Integer, nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)  # boxes * bundles
    serial_number = db.Column(db.Integer, nullable=False)

class Invoice(db.Model):
    """Sales Tax Invoice - FBR compliant"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    invoice_date = db.Column(db.Date, default=datetime.utcnow)
    invoice_time = db.Column(db.String(10))  # 24-hour e.g. 14:30:00
    invoice_type = db.Column(db.String(50), default='Tax Invoice')  # Tax Invoice/Retail Invoice/Export
    payment_mode = db.Column(db.String(30), default='Bank Transfer')  # Cash/Bank Transfer/Cheque/Credit
    hs_code = db.Column(db.String(20), default='4819.1000')
    gross_total = db.Column(db.Numeric(10, 2), nullable=False)
    sales_tax_percent = db.Column(db.Numeric(5, 2), default=18.00)
    sales_tax_amount = db.Column(db.Numeric(10, 2), nullable=False)
    income_tax_amount = db.Column(db.Numeric(10, 2), default=0)
    further_tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    # Payment details (FBR)
    payment_bank_name = db.Column(db.String(100))
    payment_account_no = db.Column(db.String(50))
    payment_transaction_id = db.Column(db.String(100))
    payment_due_date = db.Column(db.Date)
    
    # FBR Integration
    fbr_invoice_id = db.Column(db.String(22))
    qr_code_url = db.Column(db.String(500))
    fbr_timestamp = db.Column(db.DateTime)
    digital_signature = db.Column(db.Text)
    fbr_status = db.Column(db.String(20), default='Pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')

class InvoiceItem(db.Model):
    """Invoice Line Items"""
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    challan_id = db.Column(db.Integer, db.ForeignKey('challans.id'), nullable=True)
    challan_item_id = db.Column(db.Integer, db.ForeignKey('challan_items.id'), nullable=True)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_rate = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    serial_number = db.Column(db.Integer, nullable=False)

class Ledger(db.Model):
    """Customer Ledger for Accounting"""
    __tablename__ = 'ledger'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'DEBIT' or 'CREDIT'
    description = db.Column(db.String(200), nullable=False)
    reference_type = db.Column(db.String(20))  # 'INVOICE', 'PAYMENT', 'CHALLAN'
    reference_id = db.Column(db.Integer)  # ID of the related record
    debit_amount = db.Column(db.Numeric(10, 2), default=0)
    credit_amount = db.Column(db.Numeric(10, 2), default=0)
    balance = db.Column(db.Numeric(10, 2), nullable=False)  # Running balance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = db.relationship('Customer', backref='ledger_entries')

class Payment(db.Model):
    """Payment Tracking"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_mode = db.Column(db.String(20))  # Cash, Bank, Cheque
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    invoice = db.relationship('Invoice', backref='payments')
