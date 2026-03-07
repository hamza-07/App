"""
Flask Routes for Hamza Enterprises Factory Management System
"""

from flask import render_template, request, jsonify, send_file, redirect, url_for, flash
from app import app, db
import models  # Use models.Quotation etc. to avoid circular import
from utils.pdf_generator import *
from datetime import datetime, timedelta
import os

# ==================== DASHBOARD ====================
@app.route('/')
def dashboard():
    """Main Dashboard"""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    today_quotations = models.Quotation.query.filter(models.Quotation.quotation_date == today).count()
    week_quotations = models.Quotation.query.filter(models.Quotation.quotation_date >= week_start).count()
    month_quotations = models.Quotation.query.filter(models.Quotation.quotation_date >= month_start).count()

    today_challans = models.Challan.query.filter(models.Challan.challan_date == today).count()
    week_challans = models.Challan.query.filter(models.Challan.challan_date >= week_start).count()
    month_challans = models.Challan.query.filter(models.Challan.challan_date >= month_start).count()

    today_invoices = models.Invoice.query.filter(models.Invoice.invoice_date == today).count()
    week_invoices = models.Invoice.query.filter(models.Invoice.invoice_date >= week_start).count()
    month_invoices = models.Invoice.query.filter(models.Invoice.invoice_date >= month_start).count()

    pending_quotations = models.Quotation.query.filter(
        models.Quotation.status.in_(['Approved', 'Partially Delivered'])
    ).all()

    invoices_with_balance = []
    all_invoices = models.Invoice.query.order_by(models.Invoice.total_amount.desc()).limit(20).all()
    for invoice in all_invoices:
        total_paid = sum(p.amount for p in invoice.payments) if invoice.payments else 0
        if invoice.total_amount > total_paid:
            invoices_with_balance.append((invoice, invoice.customer))
            if len(invoices_with_balance) >= 10:
                break

    return render_template('dashboard.html',
        today_quotations=today_quotations,
        week_quotations=week_quotations,
        month_quotations=month_quotations,
        today_challans=today_challans,
        week_challans=week_challans,
        month_challans=month_challans,
        today_invoices=today_invoices,
        week_invoices=week_invoices,
        month_invoices=month_invoices,
        pending_quotations=pending_quotations,
        invoices_with_balance=invoices_with_balance
    )

# ==================== CUSTOMERS ====================
@app.route('/customers')
def customers():
    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    return render_template('customers/list.html', customers=customers_list)

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        customer = models.Customer(
            company_name=request.form.get('company_name'),
            customer_name=request.form.get('customer_name'),
            phone=request.form.get('phone'),
            cnic=request.form.get('cnic'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            billing_address=request.form.get('billing_address'),
            shipping_address=request.form.get('shipping_address'),
            strn=request.form.get('strn'),
            ntn=request.form.get('ntn')
        )
        db.session.add(customer)
        db.session.commit()
        create_customer_folders(customer.company_name)
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('customers/add.html')

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = models.Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.company_name = request.form.get('company_name')
        customer.customer_name = request.form.get('customer_name')
        customer.phone = request.form.get('phone')
        customer.cnic = request.form.get('cnic')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        customer.billing_address = request.form.get('billing_address')
        customer.shipping_address = request.form.get('shipping_address')
        customer.strn = request.form.get('strn')
        customer.ntn = request.form.get('ntn')
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('customers/edit.html', customer=customer)

@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    customer = models.Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted.', 'success')
    return redirect(url_for('customers'))

# ==================== SETTINGS ====================
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings_obj = models.Settings.get_settings()
    paper_grades = models.PaperGrade.query.filter_by(is_active=True).all()
    roll_grades = models.RollGrade.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        settings_obj.silicate_rate = float(request.form.get('silicate_rate', 0.0035))
        settings_obj.labour_rate = float(request.form.get('labour_rate', 0))
        settings_obj.cartage_rate = float(request.form.get('cartage_rate', 0))
        settings_obj.profit_margin_percent = float(request.form.get('profit_margin_percent', 15))
        settings_obj.wastage_percent = float(request.form.get('wastage_percent', 3))
        settings_obj.flute_factor = float(request.form.get('flute_factor', 1.4))
        settings_obj.company_name = request.form.get('company_name')
        settings_obj.company_address = request.form.get('company_address')
        settings_obj.company_phone = request.form.get('company_phone')
        settings_obj.company_strn = request.form.get('company_strn')
        settings_obj.company_ntn = request.form.get('company_ntn')
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', settings=settings_obj,
                         paper_grades=paper_grades, roll_grades=roll_grades)

@app.route('/settings/paper/add', methods=['POST'])
def add_paper_grade():
    paper = models.PaperGrade(
        name=request.json.get('name'),
        gsm=float(request.json.get('gsm')),
        rate_per_kg=float(request.json.get('rate_per_kg'))
    )
    db.session.add(paper)
    db.session.commit()
    return jsonify({'success': True, 'id': paper.id})

@app.route('/settings/roll/add', methods=['POST'])
def add_roll_grade():
    roll = models.RollGrade(
        name=request.json.get('name'),
        rate_per_roll=float(request.json.get('rate_per_roll'))
    )
    db.session.add(roll)
    db.session.commit()
    return jsonify({'success': True, 'id': roll.id})

# ==================== QUOTATIONS ====================
@app.route('/quotations')
def quotations():
    search = request.args.get('search', '')
    quotations_list = models.Quotation.query
    if search:
        quotations_list = quotations_list.join(Customer).filter(
            (models.Quotation.quotation_number.ilike(f'%{search}%')) |
            (models.Customer.company_name.ilike(f'%{search}%'))
        )
    quotations_list = quotations_list.order_by(models.Quotation.quotation_date.desc()).all()
    return render_template('quotations/list.html', quotations=quotations_list, search=search)

@app.route('/quotations/add', methods=['GET', 'POST'])
def add_quotation():
    if request.method == 'POST':
        data = request.json
        last_quote = models.Quotation.query.order_by(models.Quotation.id.desc()).first()
        quote_num = generate_quotation_number(last_quote.id if last_quote else 0)

        quotation = models.Quotation(
            quotation_number=quote_num,
            customer_id=int(data['customer_id']),
            quotation_date=datetime.strptime(data['quotation_date'], '%Y-%m-%d').date(),
            validity_days=int(data.get('validity_days', 30)),
            status='Draft',
            terms_conditions=data.get('terms_conditions')
        )
        db.session.add(quotation)
        db.session.flush()

        from utils.calculations import create_quotation_item
        for item_data in data['items']:
            item = create_quotation_item(quotation.id, item_data)
            db.session.add(item)

        db.session.commit()
        return jsonify({'success': True, 'quotation_id': quotation.id, 'quotation_number': quote_num})

    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    paper_grades = models.PaperGrade.query.filter_by(is_active=True).all()
    roll_grades = models.RollGrade.query.filter_by(is_active=True).all()
    settings_obj = models.Settings.get_settings()
    return render_template('quotations/add.html',
                         customers=customers_list,
                         paper_grades=paper_grades,
                         roll_grades=roll_grades,
                         settings=settings_obj)

@app.route('/quotations/<int:quotation_id>')
def view_quotation(quotation_id):
    quotation = models.Quotation.query.get_or_404(quotation_id)
    valid_until = quotation.quotation_date + timedelta(days=quotation.validity_days)
    return render_template('quotations/view.html', quotation=quotation, valid_until=valid_until)

@app.route('/quotations/<int:quotation_id>/approve', methods=['POST'])
def approve_quotation(quotation_id):
    quotation = models.Quotation.query.get_or_404(quotation_id)
    quotation.status = 'Approved'
    db.session.commit()
    flash('Quotation approved!', 'success')
    return redirect(url_for('view_quotation', quotation_id=quotation_id))

@app.route('/quotations/<int:quotation_id>/pdf')
def quotation_pdf(quotation_id):
    quotation = models.Quotation.query.get_or_404(quotation_id)
    pdf_path = generate_quotation_pdf(quotation)
    return send_file(pdf_path, as_attachment=True,
                    download_name=f'Quotation_{quotation.quotation_number}_{quotation.customer.company_name}.pdf')

@app.route('/quotations/<int:quotation_id>/edit', methods=['GET', 'POST'])
def edit_quotation(quotation_id):
    quotation = models.Quotation.query.get_or_404(quotation_id)
    if request.method == 'POST':
        data = request.json
        quotation.customer_id = int(data['customer_id'])
        quotation.quotation_date = datetime.strptime(data['quotation_date'], '%Y-%m-%d').date()
        quotation.validity_days = int(data.get('validity_days', 30))
        quotation.terms_conditions = data.get('terms_conditions')
        
        # Delete existing items and recreate
        models.QuotationItem.query.filter_by(quotation_id=quotation_id).delete()
        
        from utils.calculations import create_quotation_item
        for item_data in data['items']:
            item = create_quotation_item(quotation.id, item_data)
            db.session.add(item)
        
        db.session.commit()
        return jsonify({'success': True, 'quotation_id': quotation.id})
    
    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    paper_grades = models.PaperGrade.query.filter_by(is_active=True).all()
    roll_grades = models.RollGrade.query.filter_by(is_active=True).all()
    settings_obj = models.Settings.get_settings()
    
    # Prepare items for JSON
    items_json = []
    for item in quotation.items:
        items_json.append({
            'id': item.id,
            'length': item.length,
            'width': item.width,
            'height': item.height,
            'unit': item.unit,
            'ply': item.ply,
            'pcs': item.pcs,
            'quantity': item.quantity,
            'joint_type': item.joint_type,
            'top_paper_id': item.top_paper_id,
            'middle_paper_id': item.middle_paper_id,
            'bottom_paper_id': item.bottom_paper_id,
            'flute1_roll_id': item.flute1_roll_id,
            'flute2_roll_id': item.flute2_roll_id,
            'flute3_roll_id': item.flute3_roll_id,
            'printing_cost': item.printing_cost or 0,
            'labour_cost': item.labour_cost or 0,
            'cartage_cost': item.cartage_cost or 0,
            'use_manual_rate': item.use_manual_rate or False,
            'description': item.description,
            'manual_rate': item.manual_rate
        })
    
    return render_template('quotations/edit_new.html', 
                         quotation=quotation,
                         customers=customers_list,
                         paper_grades=paper_grades,
                         roll_grades=roll_grades,
                         settings=settings_obj,
                         items_json=items_json)

@app.route('/quotations/<int:quotation_id>/delete', methods=['POST'])
def delete_quotation(quotation_id):
    quotation = models.Quotation.query.get_or_404(quotation_id)
    models.QuotationItem.query.filter_by(quotation_id=quotation_id).delete()
    db.session.delete(quotation)
    db.session.commit()
    flash('Quotation deleted.', 'success')
    return redirect(url_for('quotations'))

@app.route('/api/customers/<int:customer_id>/quotations')
def get_customer_quotations(customer_id):
    """Return approved quotations for a customer (for challan add page)."""
    quotations = models.Quotation.query.filter(
        models.Quotation.customer_id == customer_id,
        models.Quotation.status.in_(['Approved', 'Partially Delivered'])
    ).order_by(models.Quotation.quotation_date.desc()).all()
    return jsonify([{
        'id': q.id,
        'quotation_number': q.quotation_number,
        'quotation_date': q.quotation_date.strftime('%Y-%m-%d'),
        'customer_id': q.customer_id
    } for q in quotations])

@app.route('/api/quotations/<int:quotation_id>/items')
def get_quotation_items(quotation_id):
    quotation = models.Quotation.query.get_or_404(quotation_id)
    items = []
    for item in quotation.items:
        delivered = sum(ci.total_quantity for challan in quotation.challans
                       for ci in challan.items if ci.quotation_item_id == item.id)
        pending = item.quantity - delivered
        items.append({
            'id': item.id,
            'description': item.description,
            'quantity': item.quantity,
            'delivered': delivered,
            'pending': pending
        })
    return jsonify(items)

# ==================== CHALLANS ====================
@app.route('/challans')
def challans():
    challans_list = models.Challan.query.order_by(models.Challan.challan_date.desc()).all()
    return render_template('challans/list.html', challans=challans_list)

@app.route('/challans/add', methods=['GET', 'POST'])
def add_challan():
    if request.method == 'POST':
        data = request.json
        last_challan = models.Challan.query.order_by(models.Challan.id.desc()).first()
        challan_num = generate_challan_number(last_challan.id if last_challan else 0)

        challan = models.Challan(
            challan_number=challan_num,
            quotation_id=int(data['quotation_id']) if data.get('quotation_id') else None,
            customer_id=int(data['customer_id']),
            challan_date=datetime.strptime(data['challan_date'], '%Y-%m-%d').date(),
            po_number=data.get('po_number'),
            driver_name=data.get('driver_name'),
            vehicle_no=data.get('vehicle_no'),
            driver_contact=data.get('driver_contact')
        )
        db.session.add(challan)
        db.session.flush()

        for idx, item_data in enumerate(data['items'], 1):
            item = models.ChallanItem(
                challan_id=challan.id,
                quotation_item_id=item_data.get('quotation_item_id'),
                description=item_data['description'],
                boxes=int(item_data['boxes']),
                bundles=int(item_data['bundles']),
                total_quantity=int(item_data['boxes']) * int(item_data['bundles']),
                serial_number=idx
            )
            db.session.add(item)

        if challan.quotation_id:
            quotation = models.Quotation.query.get(challan.quotation_id)
            pending = quotation.get_pending_quantity()
            if pending == 0:
                quotation.status = 'Closed'
            elif pending < quotation.get_total_quantity():
                quotation.status = 'Partially Delivered'

        db.session.commit()
        return jsonify({'success': True, 'challan_id': challan.id, 'challan_number': challan_num})

    quotations_list = models.Quotation.query.filter(models.Quotation.status.in_(['Approved', 'Partially Delivered'])).all()
    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    return render_template('challans/add.html', quotations=quotations_list, customers=customers_list)

@app.route('/challans/<int:challan_id>/edit', methods=['GET', 'POST'])
def edit_challan(challan_id):
    challan = models.Challan.query.get_or_404(challan_id)
    if request.method == 'POST':
        data = request.json
        challan.quotation_id = int(data['quotation_id']) if data.get('quotation_id') else None
        challan.customer_id = int(data['customer_id'])
        challan.challan_date = datetime.strptime(data['challan_date'], '%Y-%m-%d').date()
        challan.po_number = data.get('po_number')
        challan.driver_name = data.get('driver_name')
        challan.vehicle_no = data.get('vehicle_no')
        challan.driver_contact = data.get('driver_contact')
        
        # Delete existing items and recreate
        models.ChallanItem.query.filter_by(challan_id=challan_id).delete()
        
        for idx, item_data in enumerate(data['items'], 1):
            item = models.ChallanItem(
                challan_id=challan.id,
                quotation_item_id=item_data.get('quotation_item_id'),
                description=item_data['description'],
                boxes=int(item_data['boxes']),
                bundles=int(item_data['bundles']),
                total_quantity=int(item_data['boxes']) * int(item_data['bundles']),
                serial_number=idx
            )
            db.session.add(item)
        
        db.session.commit()
        return jsonify({'success': True, 'challan_id': challan.id})
    
    quotations_list = models.Quotation.query.filter(models.Quotation.status.in_(['Approved', 'Partially Delivered'])).all()
    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    return render_template('challans/edit.html', 
                         challan=challan,
                         quotations=quotations_list, 
                         customers=customers_list)

@app.route('/challans/<int:challan_id>/pdf')
def challan_pdf(challan_id):
    challan = models.Challan.query.get_or_404(challan_id)
    pdf_path = generate_challan_pdf(challan)
    return send_file(pdf_path, as_attachment=True,
                    download_name=f'Challan_{challan.challan_number}_{challan.customer.company_name}.pdf')

@app.route('/challans/<int:challan_id>/delete', methods=['POST'])
def delete_challan(challan_id):
    """Delete a challan"""
    challan = models.Challan.query.get_or_404(challan_id)
    
    # Update quotation status if linked
    if challan.quotation_id:
        quotation = models.Quotation.query.get(challan.quotation_id)
        if quotation:
            # Check if there are other challans
            remaining_challans = models.Challan.query.filter(
                models.Challan.quotation_id == quotation.id,
                models.Challan.id != challan_id
            ).count()
            
            if remaining_challans == 0:
                quotation.status = 'Approved'
            else:
                quotation.status = 'Partially Delivered'
    
    # Delete challan items
    models.ChallanItem.query.filter_by(challan_id=challan_id).delete()
    
    # Delete challan
    db.session.delete(challan)
    db.session.commit()
    
    flash('Challan deleted successfully', 'success')
    return redirect(url_for('challans'))

# ==================== INVOICES ====================
@app.route('/invoices')
def invoices():
    invoices_list = models.Invoice.query.order_by(models.Invoice.invoice_date.desc()).all()
    return render_template('invoices/list.html', invoices=invoices_list)

@app.route('/invoices/add', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        data = request.json
        challan_ids = [int(cid) for cid in data.get('challan_ids', [])]
        challans = models.Challan.query.filter(models.Challan.id.in_(challan_ids)).all() if challan_ids else []

        if challans:
            customer_ids = set(c.customer_id for c in challans)
            if len(customer_ids) > 1:
                return jsonify({'success': False, 'message': 'All challans must be from the same customer'})
            customer_id = list(customer_ids)[0]
        else:
            customer_id = int(data['customer_id'])

        last_invoice = models.Invoice.query.order_by(models.Invoice.id.desc()).first()
        invoice_num = generate_invoice_number(last_invoice.id if last_invoice else 0)

        gross_total = sum(float(item['amount']) for item in data['items'])
        sales_tax_percent = float(data.get('sales_tax_percent', 18))
        sales_tax_amount = gross_total * (sales_tax_percent / 100)
        income_tax_amount = float(data.get('income_tax_amount', 0))
        further_tax_amount = float(data.get('further_tax_amount', 0))
        total_amount = gross_total + sales_tax_amount + income_tax_amount + further_tax_amount

        invoice = models.Invoice(
            invoice_number=invoice_num,
            customer_id=customer_id,
            invoice_date=datetime.strptime(data['invoice_date'], '%Y-%m-%d').date(),
            hs_code=data.get('hs_code', '4819.1000'),
            gross_total=gross_total,
            sales_tax_percent=sales_tax_percent,
            sales_tax_amount=sales_tax_amount,
            income_tax_amount=income_tax_amount,
            further_tax_amount=further_tax_amount,
            total_amount=total_amount
        )
        db.session.add(invoice)
        db.session.flush()

        for idx, item_data in enumerate(data['items'], 1):
            item = models.InvoiceItem(
                invoice_id=invoice.id,
                challan_id=int(item_data['challan_id']) if item_data.get('challan_id') else None,
                challan_item_id=int(item_data['challan_item_id']) if item_data.get('challan_item_id') else None,
                description=item_data['description'],
                quantity=int(item_data['quantity']),
                unit_rate=float(item_data['unit_rate']),
                amount=float(item_data['amount']),
                serial_number=idx
            )
            db.session.add(item)

        if challan_ids:
            models.Challan.query.filter(models.Challan.id.in_(challan_ids)).update({'is_invoiced': True}, synchronize_session=False)

        db.session.commit()
        return jsonify({'success': True, 'invoice_id': invoice.id, 'invoice_number': invoice_num})

    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    return render_template('invoices/add.html', customers=customers_list)

@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    invoice = models.Invoice.query.get_or_404(invoice_id)
    if request.method == 'POST':
        data = request.json
        invoice.invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
        invoice.hs_code = data.get('hs_code', '4819.1000')
        
        # Update items
        models.InvoiceItem.query.filter_by(invoice_id=invoice_id).delete()
        
        gross_total = sum(float(item['amount']) for item in data['items'])
        sales_tax_percent = float(data.get('sales_tax_percent', 18))
        sales_tax_amount = gross_total * (sales_tax_percent / 100)
        income_tax_amount = float(data.get('income_tax_amount', 0))
        further_tax_amount = float(data.get('further_tax_amount', 0))
        total_amount = gross_total + sales_tax_amount + income_tax_amount + further_tax_amount
        
        invoice.gross_total = gross_total
        invoice.sales_tax_percent = sales_tax_percent
        invoice.sales_tax_amount = sales_tax_amount
        invoice.income_tax_amount = income_tax_amount
        invoice.further_tax_amount = further_tax_amount
        invoice.total_amount = total_amount
        
        for idx, item_data in enumerate(data['items'], 1):
            item = models.InvoiceItem(
                invoice_id=invoice.id,
                challan_id=int(item_data['challan_id']) if item_data.get('challan_id') else None,
                challan_item_id=int(item_data['challan_item_id']) if item_data.get('challan_item_id') else None,
                description=item_data['description'],
                quantity=int(item_data['quantity']),
                unit_rate=float(item_data['unit_rate']),
                amount=float(item_data['amount']),
                serial_number=idx
            )
            db.session.add(item)
        
        db.session.commit()
        return jsonify({'success': True, 'invoice_id': invoice.id})
    
    customers_list = models.Customer.query.order_by(models.Customer.company_name).all()
    return render_template('invoices/edit.html', 
                         invoice=invoice,
                         customers=customers_list)

@app.route('/invoices/<int:invoice_id>/pdf')
def invoice_pdf(invoice_id):
    invoice = models.Invoice.query.get_or_404(invoice_id)
    pdf_path = generate_invoice_pdf(invoice)
    return send_file(pdf_path, as_attachment=True,
                    download_name=f'Invoice_{invoice.invoice_number}_{invoice.customer.company_name}.pdf')

@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice(invoice_id):
    """Delete invoice"""
    invoice = models.Invoice.query.get_or_404(invoice_id)

    models.InvoiceItem.query.filter_by(invoice_id=invoice_id).delete()

    challan_ids = [item.challan_id for item in invoice.items if item.challan_id]
    if challan_ids:
        models.Challan.query.filter(models.Challan.id.in_(challan_ids)).update({'is_invoiced': False}, synchronize_session=False)

    db.session.delete(invoice)
    db.session.commit()

    flash('Invoice deleted successfully', 'success')
    return redirect(url_for('invoices'))

@app.route('/api/challans/uninvoiced')
def get_uninvoiced_challans():
    """Get uninvoiced challans for a customer"""
    customer_id = request.args.get('customer_id')
    challans = models.Challan.query.filter_by(
        customer_id=customer_id,
        is_invoiced=False
    ).all()

    result = []
    for challan in challans:
        result.append({
            'id': challan.id,
            'challan_number': challan.challan_number,
            'date': challan.challan_date.strftime('%Y-%m-%d'),
            'items': [{
                'id': item.id,
                'description': item.description,
                'total_quantity': item.total_quantity
            } for item in challan.items]
        })
    return jsonify(result)

# ==================== PAYMENTS ====================
@app.route('/payments')
def payments():
    """List all payments"""
    payments_list = models.Payment.query.order_by(models.Payment.payment_date.desc()).all()
    return render_template('payments/list.html', payments=payments_list)

@app.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    """Add payment"""
    if request.method == 'GET':
        invoice_id = request.args.get('invoice_id')
        invoice = models.Invoice.query.get_or_404(invoice_id) if invoice_id else None
        return render_template('payments/add.html', invoice=invoice)

    payment = models.Payment(
        invoice_id=int(request.json['invoice_id']),
        payment_date=datetime.strptime(request.json['payment_date'], '%Y-%m-%d').date(),
        amount=float(request.json['amount']),
        payment_mode=request.json.get('payment_mode'),
        reference_number=request.json.get('reference_number'),
        notes=request.json.get('notes')
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify({'success': True})

# ==================== HELPERS ====================
def generate_quotation_number(last_id):
    return f"HHQ/{str(last_id + 1).zfill(4)}"

def generate_challan_number(last_id):
    return f"HHE/CH/{str(last_id + 1).zfill(4)}"

def generate_invoice_number(last_id):
    return f"HHE/INV/{str(last_id + 1).zfill(4)}"

def create_customer_folders(company_name):
    base_path = app.config['PDF_FOLDER']
    safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
    folders = [
        os.path.join(base_path, safe_name),
        os.path.join(base_path, safe_name, 'Challans'),
        os.path.join(base_path, safe_name, 'Bills')
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
