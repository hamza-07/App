"""
PDF Generation Utilities using ReportLab
Generates Quotation, Challan, and Invoice PDFs with proper formatting
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import os
from app import app

def get_letterhead_image_path(filename):
    """Get path to letterhead image"""
    return os.path.join('static', 'images', filename)

def generate_quotation_pdf(quotation):
    """Generate Quotation PDF"""
    from models import Settings
    customer = quotation.customer
    settings = Settings.get_settings()
    
    # File path
    safe_name = "".join(c for c in customer.company_name if c.isalnum() or c in (' ', '-', '_')).strip()
    folder = os.path.join(app.config['PDF_FOLDER'], safe_name)
    os.makedirs(folder, exist_ok=True)
    
    quote_num_safe = (quotation.quotation_number or '').replace('/', '-')
    filename = f"Quotation_{quote_num_safe}_{safe_name}_{quotation.quotation_date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join(folder, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0, bottomMargin=20*mm)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Letterhead (if exists)
    letterhead_path = get_letterhead_image_path('Latterhead.png')
    if os.path.exists(letterhead_path):
        img = Image(letterhead_path, width=A4[0], height=100*mm, kind='proportional')
        story.append(img)
        story.append(Spacer(1, 5*mm))
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    story.append(Paragraph("QUOTATION", title_style))
    story.append(Spacer(1, 5*mm))
    
    # Quotation Details
    data = [
        ['Quotation No:', quotation.quotation_number, 'Date:', quotation.quotation_date.strftime('%d-%m-%Y')],
        ['Customer:', customer.company_name, 'Valid Until:', (quotation.quotation_date + timedelta(days=quotation.validity_days)).strftime('%d-%m-%Y')],
    ]
    
    if customer.address:
        data.append(['Address:', customer.address, '', ''])
    if customer.strn:
        data.append(['STN:', customer.strn, 'NTN:', customer.ntn or ''])
    
    table = Table(data, colWidths=[40*mm, 80*mm, 30*mm, 50*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 10*mm))
    
    # Items Table
    items_data = [['Sr#', 'Description', 'Qty', 'Unit Rate (PKR)', 'Total (PKR)']]
    total_amount = 0
    
    for idx, item in enumerate(quotation.items, 1):
        is_rate_only = getattr(item, 'use_manual_rate', False) or (getattr(item, 'quantity', 1) == 0)
        qty_str = '—' if is_rate_only else str(item.quantity)
        total_str = 'Per unit' if is_rate_only else f"{item.total_amount:.2f}"
        if not is_rate_only:
            total_amount += float(item.total_amount)
        items_data.append([
            str(idx),
            item.description,
            qty_str,
            f"{item.unit_rate:.2f}",
            total_str
        ])
    
    # Total row
    items_data.append(['', '', '', 'Total:', f"{total_amount:.2f}"])
    
    items_table = Table(items_data, colWidths=[15*mm, 100*mm, 20*mm, 30*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -2), 'LEFT'),
        ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
        ('FONTNAME', (4, -1), (4, -1), 'Helvetica-Bold'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10*mm))
    
    # Terms & Conditions
    if quotation.terms_conditions:
        story.append(Paragraph("<b>Terms & Conditions:</b>", styles['Heading2']))
        story.append(Paragraph(quotation.terms_conditions, styles['Normal']))
        story.append(Spacer(1, 10*mm))
    
    # Signature area
    story.append(Spacer(1, 20*mm))
    sig_data = [
        ['', ''],
        ['Authorized Signature', 'Customer Signature']
    ]
    sig_table = Table(sig_data, colWidths=[90*mm, 90*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return filepath

def generate_challan_pdf(challan):
    """Generate Delivery Challan PDF (2-in-1 page: Original + Duplicate)"""
    customer = challan.customer
    
    # File path
    safe_name = "".join(c for c in customer.company_name if c.isalnum() or c in (' ', '-', '_')).strip()
    folder = os.path.join(app.config['PDF_FOLDER'], safe_name, 'Challans')
    os.makedirs(folder, exist_ok=True)
    
    challan_num_safe = (challan.challan_number or '').replace('/', '-')
    filename = f"Challan_{challan_num_safe}_{safe_name}_{challan.challan_date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join(folder, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0, bottomMargin=10*mm)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Create two copies on one page
    for copy_type in ['ORIGINAL COPY', 'DUPLICATE COPY']:
        # Letterhead
        letterhead_path = get_letterhead_image_path('Latterhead.png')
        if os.path.exists(letterhead_path):
            img = Image(letterhead_path, width=A4[0], height=50*mm, kind='proportional')
            story.append(img)
            story.append(Spacer(1, 2*mm))
        
        # Copy label
        copy_style = ParagraphStyle(
            'CopyLabel',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#000000'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(copy_type, copy_style))
        story.append(Spacer(1, 3*mm))
        
        # Challan Details
        data = [
            ['Challan No:', challan.challan_number],
            ['Party Name:', customer.company_name],
            ['M/s:', customer.company_name],
            ['Date:', challan.challan_date.strftime('%d-%m-%Y')],
        ]
        
        if challan.po_number:
            data.append(['P.O. No:', challan.po_number])
        if challan.driver_name:
            data.append(['Driver:', challan.driver_name])
        if challan.vehicle_no:
            data.append(['Vehicle No:', challan.vehicle_no])
        
        table = Table(data, colWidths=[40*mm, 150*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 5*mm))
        
        # Items Table (Total = good qty + loss)
        items_data = [['Sr#', 'Description', 'Boxes', 'Bundles', 'Loss', 'Total']]
        for item in challan.items:
            loss = getattr(item, 'loss_quantity', 0) or 0
            total_with_loss = item.total_quantity + loss
            items_data.append([
                str(item.serial_number),
                item.description,
                str(item.boxes),
                str(item.bundles),
                str(loss),
                str(total_with_loss)
            ])
        
        items_table = Table(items_data, colWidths=[12*mm, 75*mm, 20*mm, 20*mm, 18*mm, 25*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 8*mm))
        
        # Signature area
        sig_data = [
            ['', ''],
            ['Receiver\'s Signature', 'Authorized Signature']
        ]
        sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
        ]))
        story.append(sig_table)
        
        # Add separator between copies (except for last)
        if copy_type == 'ORIGINAL COPY':
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("─" * 80, styles['Normal']))
            story.append(Spacer(1, 5*mm))
    
    doc.build(story)
    return filepath

def _fbr_qr_content(invoice, settings):
    """FBR QR content: SellerName|STRN|InvoiceNo|DateTime|TotalAmount|SalesTax|BuyerName|BuyerNTN"""
    from io import BytesIO
    customer = invoice.customer
    inv_date = invoice.invoice_date
    inv_time = getattr(invoice, 'invoice_time', None) or datetime.now().strftime('%H:%M:%S')
    dt_str = f"{inv_date.strftime('%Y-%m-%d')} {inv_time}"
    seller_name = (getattr(settings, 'company_name', None) or 'HAMZA ENTERPRISES').replace('|', ' ')
    seller_strn = (getattr(settings, 'company_strn', None) or '')
    buyer_name = (customer.company_name or '').replace('|', ' ')
    buyer_ntn = (customer.ntn or customer.cnic or '')
    total = float(invoice.total_amount)
    tax = float(invoice.sales_tax_amount)
    content = f"{seller_name}|{seller_strn}|{invoice.invoice_number}|{dt_str}|{total:.0f}|{tax:.0f}|{buyer_name}|{buyer_ntn}"
    return content


def _generate_fbr_qr_image(invoice, settings, size_mm=20):
    """Generate QR code image for FBR (min 2cm x 2cm). Returns path or None."""
    try:
        import qrcode
        content = _fbr_qr_content(invoice, settings)
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        folder = os.path.join(app.config['PDF_FOLDER'], 'fbr_qr')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"qr_{invoice.id}_{invoice.invoice_number.replace('/', '-')}.png")
        img.save(path)
        return path
    except Exception:
        return None


def generate_invoice_pdf(invoice):
    """Generate FBR-compliant Sales Tax Invoice PDF (Original + Duplicate pages)."""
    from models import Settings
    from utils.amount_to_words import amount_to_words_pkr

    customer = invoice.customer
    settings = Settings.get_settings()
    # Safe get for new columns (existing DB may not have them)
    invoice_time = getattr(invoice, 'invoice_time', None) or datetime.now().strftime('%H:%M:%S')
    invoice_type = getattr(invoice, 'invoice_type', None) or 'Tax Invoice'
    payment_mode = getattr(invoice, 'payment_mode', None) or 'Bank Transfer'
    discount_amount = getattr(invoice, 'discount_amount', None) or 0
    discount_amount = float(discount_amount)

    safe_name = "".join(c for c in customer.company_name if c.isalnum() or c in (' ', '-', '_')).strip()
    folder = os.path.join(app.config['PDF_FOLDER'], safe_name, 'Bills')
    os.makedirs(folder, exist_ok=True)
    invoice_num_safe = (invoice.invoice_number or '').replace('/', '-')
    filename = f"Invoice_{invoice_num_safe}_{safe_name}_{invoice.invoice_date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join(folder, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0, bottomMargin=15*mm)
    story = []
    styles = getSampleStyleSheet()
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9, spaceAfter=2)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', spaceAfter=2)

    challan_nos = list(set(item.challan.challan_number for item in invoice.items if item.challan))
    po_nos = list(set(item.challan.po_number for item in invoice.items if item.challan and item.challan.po_number))

    for copy_type in ['ORIGINAL', 'DUPLICATE']:
        # Letterhead
        letterhead_path = get_letterhead_image_path('Latterhead1.png')
        if os.path.exists(letterhead_path):
            story.append(Image(letterhead_path, width=A4[0], height=80*mm, kind='proportional'))
            story.append(Spacer(1, 3*mm))

        # Header
        story.append(Paragraph("SALES TAX INVOICE", ParagraphStyle('H1', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER)))
        story.append(Paragraph(f"({copy_type} Copy)", ParagraphStyle('H2', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)))
        story.append(Spacer(1, 4*mm))

        # Section 1: Header info
        header_data = [
            ['Invoice No:', invoice.invoice_number, 'Invoice Date:', invoice.invoice_date.strftime('%d-%b-%Y')],
            ['Invoice Time:', invoice_time, 'Invoice Type:', invoice_type],
            ['Payment Mode:', payment_mode, '', ''],
        ]
        if challan_nos:
            header_data.append(['DC No:', ', '.join(challan_nos), '', ''])
        if po_nos:
            header_data.append(['PO No:', ', '.join(po_nos), '', ''])
        t1 = Table(header_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
        t1.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 9)]))
        story.append(t1)
        story.append(Spacer(1, 4*mm))

        # Section 2: Seller
        seller_name = getattr(settings, 'company_name', None) or 'HAMZA HUSSAIN ENTERPRISES PAKISTAN (PVT) LTD'
        story.append(Paragraph("SELLER:", bold_style))
        story.append(Paragraph(seller_name, small_style))
        story.append(Paragraph("Address: " + (getattr(settings, 'company_address', None) or ''), small_style))
        story.append(Paragraph(f"STRN: {getattr(settings, 'company_strn', None) or ''} | NTN: {getattr(settings, 'company_ntn', None) or ''}", small_style))
        story.append(Paragraph(f"Phone: {getattr(settings, 'company_phone', None) or ''} | Email: {getattr(settings, 'company_email', None) or ''}", small_style))
        story.append(Paragraph("Business Type: " + (getattr(settings, 'business_type', None) or 'Manufacturer'), small_style))
        story.append(Spacer(1, 3*mm))

        # Section 3: Buyer
        story.append(Paragraph("BUYER:", bold_style))
        story.append(Paragraph(customer.company_name or '', small_style))
        story.append(Paragraph("Address: " + (customer.billing_address or customer.address or ''), small_style))
        story.append(Paragraph(f"STRN: {customer.strn or 'Unregistered'} | NTN: {customer.ntn or ''}", small_style))
        if customer.cnic:
            story.append(Paragraph(f"CNIC: {customer.cnic} | Phone: {customer.phone or ''}", small_style))
        else:
            story.append(Paragraph("Phone: " + (customer.phone or ''), small_style))
        story.append(Paragraph("Customer Type: " + ("Registered" if customer.strn else "Unregistered"), small_style))
        story.append(Spacer(1, 4*mm))

        # Section 4: Items table (Sr#, Description, HS Code, Qty, Unit, Rate(PKR), Amount(PKR), Sales Tax)
        hs = invoice.hs_code or '4819.1000'
        tax_pct = float(invoice.sales_tax_percent or 18)
        items_data = [['Sr#', 'Description of Goods/Services', 'HS Code', 'Qty', 'Unit', 'Rate(PKR)', 'Amount(PKR)', 'Sales Tax']]
        for item in invoice.items:
            amt = float(item.amount)
            line_tax = round(amt * (tax_pct / 100), 2)
            items_data.append([
                str(item.serial_number),
                item.description[:40] + ('...' if len(item.description) > 40 else ''),
                hs,
                str(item.quantity),
                'PCS',
                f"{float(item.unit_rate):,.2f}",
                f"{amt:,.2f}",
                f"{line_tax:,.2f}"
            ])
        col_w = [8*mm, 55*mm, 18*mm, 12*mm, 12*mm, 22*mm, 25*mm, 20*mm]
        t2 = Table(items_data, colWidths=col_w)
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (7, -1), 'RIGHT'),
        ]))
        story.append(t2)
        story.append(Spacer(1, 4*mm))

        # Section 5: Tax calculation summary
        gross = float(invoice.gross_total)
        stax = float(invoice.sales_tax_amount)
        ftax = float(invoice.further_tax_amount or 0)
        total = float(invoice.total_amount)
        tax_data = [
            ['Taxable Value:', f"PKR {gross:,.2f}"],
            ['Add: Sales Tax @ ' + str(int(tax_pct)) + '%:', f"PKR {stax:,.2f}"],
        ]
        if ftax > 0:
            tax_data.append(['Add: Further Tax @ 3%:', f"PKR {ftax:,.2f}"])
        if discount_amount > 0:
            tax_data.append(['Less: Discount:', f"PKR {discount_amount:,.2f}"])
        tax_data.append(['GRAND TOTAL:', f"PKR {total:,.2f}"])
        t3 = Table(tax_data, colWidths=[80*mm, 50*mm])
        t3.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        story.append(t3)
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("<b>Amount in Words:</b> " + amount_to_words_pkr(total), small_style))
        story.append(Spacer(1, 4*mm))

        # Section 6: Payment details (optional fields)
        payment_bank = getattr(invoice, 'payment_bank_name', None)
        payment_acct = getattr(invoice, 'payment_account_no', None)
        payment_txn = getattr(invoice, 'payment_transaction_id', None)
        payment_due = getattr(invoice, 'payment_due_date', None)
        if payment_bank or payment_txn:
            story.append(Paragraph("PAYMENT DETAILS:", bold_style))
            if payment_bank:
                story.append(Paragraph(f"Payment Mode: {payment_mode} | Bank: {payment_bank}", small_style))
            if payment_acct:
                story.append(Paragraph(f"Account No: {payment_acct}", small_style))
            if payment_txn:
                story.append(Paragraph(f"Transaction ID: {payment_txn}", small_style))
            if payment_due:
                story.append(Paragraph(f"Due Date: {payment_due.strftime('%d-%b-%Y')}", small_style))
            story.append(Spacer(1, 3*mm))

        # Section 7: QR code (FBR - min 2cm x 2cm) + Signatures side by side
        qr_path = _generate_fbr_qr_image(invoice, settings)
        sig_left = "Receiver's Signature<br/>Name: _________________<br/>Date: _________________"
        sig_right = "Authorized Signature<br/>For " + (getattr(settings, 'company_name', None) or 'HAMZA ENTERPRISES')[:30] + "<br/>Name: _________________<br/>Date: _________________"
        if qr_path and os.path.exists(qr_path):
            qr_img = Image(qr_path, width=20*mm, height=20*mm)
            layout_data = [[Paragraph(sig_left, small_style), Paragraph(sig_right, small_style), qr_img]]
        else:
            layout_data = [[Paragraph(sig_left, small_style), Paragraph(sig_right, small_style), Paragraph('', small_style)]]
        t4 = Table(layout_data, colWidths=[70*mm, 70*mm, 25*mm])
        t4.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTSIZE', (0, 0), (1, -1), 9)]))
        story.append(t4)
        story.append(Spacer(1, 3*mm))

        # Declaration
        story.append(Paragraph("DECLARATION:", bold_style))
        decl = "We certify that this invoice shows the actual price of the goods described and that all particulars are true and correct. Sales tax has been charged as per Sales Tax Act, 1990."
        story.append(Paragraph(decl, ParagraphStyle('Decl', parent=styles['Normal'], fontSize=8, spaceAfter=2)))
        story.append(Paragraph("COMPANY STAMP: _________________", small_style))

        if copy_type == 'ORIGINAL':
            story.append(PageBreak())

    doc.build(story)
    return filepath
