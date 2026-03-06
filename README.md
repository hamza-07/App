# Hamza Enterprises - Factory Management System

A comprehensive Flask web application for managing a corrugation and packaging factory workflow: **Quotation → Delivery Challan → Sales Tax Invoice**.

## Features

### Core Workflow
- **Customer Management**: Add and manage customers with billing/shipping addresses
- **Quotation Module**: Create quotations with automatic cost calculations based on carton specifications
- **Delivery Challan**: Generate delivery challans linked to quotations (2-in-1 page PDF)
- **Sales Tax Invoice**: Create invoices from challans with 18% GST calculation
- **FBR Integration**: Submit invoices to FBR (Federal Board of Revenue) for digital invoicing

### Key Calculations
- Automatic unit conversion (mm/cm to inches)
- Roll size and cutting size calculations
- Paper cost calculations based on GSM and grade
- Silicate rate calculations with ply factors
- Profit margin application
- Multi-item quotations support

### Additional Features
- **Dashboard**: Sales overview, pending deliveries, outstanding balances
- **Settings**: Manage paper grades, roll grades, rates, and company information
- **Payment Tracking**: Record payments against invoices
- **PDF Generation**: Professional PDFs with company letterhead
- **Search**: Find quotations, challans, and invoices quickly

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your SECRET_KEY and FBR_API_TOKEN (if using FBR)
```

4. **Initialize the database:**
```bash
python app.py
```
This will create the SQLite database and all necessary tables.

5. **Run the application:**
```bash
python app.py
```

6. **Access the application:**
Open your browser and go to `http://localhost:5000`

## Initial Setup

1. **Add Company Letterhead Images:**
   - Place `Latterhead.png` in `static/images/` (for Quotations and Challans)
   - Place `Latterhead1.png` in `static/images/` (for Invoices)

2. **Configure Settings:**
   - Go to Settings page
   - Add your company information
   - Add Paper Grades (e.g., Kraft 125g, Fluting 115g)
   - Add Roll Grades with rates
   - Set default rates (Silicate, Labour, Cartage, Profit Margin)

3. **Add Customers:**
   - Go to Customers page
   - Add your first customer with all required details

## Usage

### Creating a Quotation
1. Go to Quotations → New Quotation
2. Select customer
3. Add items with:
   - Dimensions (L, W, H) in mm/cm/inches
   - Ply (3, 5, or 7)
   - Paper selections for each layer
   - Roll selections
   - Quantity
4. System calculates unit rate automatically
5. Save and approve quotation

### Creating a Delivery Challan
1. Go to Challans → New Challan
2. Select quotation (optional) or customer directly
3. Add delivery items (Boxes × Bundles = Total Quantity)
4. Add driver and vehicle information
5. Save and download PDF

### Creating an Invoice
1. Go to Invoices → New Invoice
2. Select customer
3. Select one or more challans
4. Enter unit rates for each item
5. System calculates 18% GST automatically
6. Save and download PDF
7. Optionally submit to FBR

## Database

The application uses SQLite by default (can be changed to PostgreSQL for production). Database file: `hamza_enterprises.db`

## File Storage

PDFs are automatically saved in:
```
generated_pdfs/
  └── [Customer Name]/
      ├── Challans/
      │   └── Challan_[Number]_[Date].pdf
      └── Bills/
          └── Invoice_[Number]_[Date].pdf
```

## FBR Integration

To enable FBR digital invoicing:
1. Get FBR API credentials
2. Add `FBR_API_TOKEN` to `.env`
3. When creating an invoice, click "Submit to FBR" button
4. System will generate QR code and FBR Invoice ID

## Mobile Access

The application is responsive and works on mobile browsers. Access it from any device using the same URL.

## Production Deployment

For production:
1. Change `SECRET_KEY` in `.env`
2. Use PostgreSQL instead of SQLite (update `DATABASE_URL`)
3. Use a production WSGI server (gunicorn, uWSGI)
4. Set up proper domain and SSL certificate
5. Configure reverse proxy (nginx)

## Support

For issues or questions, please refer to the documentation or contact support.

## License

Proprietary - Hamza Enterprises
