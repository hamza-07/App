# Quick Start Guide - Hamza Enterprises Factory Management System

## First Time Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Add Letterhead Images
1. Place your company letterhead images in `static/images/`:
   - `Latterhead.png` - For Quotations and Challans
   - `Latterhead1.png` - For Invoices

### Step 3: Run the Application
```bash
python app.py
```

The application will:
- Create the database automatically
- Start on `http://localhost:5000`

### Step 4: Initial Configuration

1. **Go to Settings** (`/settings`)
   - Add your company name, address, STN, NTN
   - Set default rates (Silicate, Labour, Cartage)
   - Set Profit Margin % (default: 15%)

2. **Add Paper Grades**
   - Click "Add Paper Grade" button
   - Example: "Kraft 125g", GSM: 125, Rate: 50 PKR/kg

3. **Add Roll Grades**
   - Click "Add Roll Grade" button
   - Example: "Standard Roll", Rate: 5000 PKR/roll

4. **Add Your First Customer**
   - Go to Customers → Add New Customer
   - Fill in: Company Name, Phone, Address, STN, NTN

### Step 5: Create Your First Quotation

1. Go to **Quotations → New Quotation**
2. Select customer
3. Click "Add Item"
4. Enter:
   - Length, Width, Height (in mm, cm, or inches)
   - Select Ply (3, 5, or 7)
   - Select Papers for each layer
   - Select Roll grades
   - Enter Quantity
5. System calculates rate automatically
6. Click "Save Quotation"
7. Click "Approve Quotation"

### Step 6: Create Delivery Challan

1. Go to **Challans → New Challan**
2. Select the approved quotation
3. System auto-fills items
4. Enter Boxes and Bundles for each item
5. Add driver and vehicle info
6. Click "Save Challan"
7. PDF downloads automatically

### Step 7: Create Invoice

1. Go to **Invoices → New Invoice**
2. Select customer
3. Click "Load Challans"
4. Check the challans you want to invoice
5. Enter unit rates for each item
6. System calculates 18% GST automatically
7. Click "Save Invoice"
8. PDF downloads automatically

## Workflow Summary

```
Customer → Quotation → Approve → Challan → Invoice → Payment
```

## Key Features

✅ **Automatic Calculations**
- Unit conversion (mm/cm → inches)
- Roll size and cutting size
- Paper costs based on GSM
- Silicate with ply factors
- Profit margin application

✅ **PDF Generation**
- Professional formatting
- Company letterhead
- 2-in-1 page for Challans
- Separate pages for Invoices

✅ **FBR Integration** (Optional)
- Submit invoices to FBR
- Get 22-digit FBR Invoice ID
- QR code generation

## Common Tasks

### Search Quotation
- Go to Quotations page
- Use search box (by number or customer name)

### View Pending Deliveries
- Dashboard shows all approved quotations not yet fully delivered

### Track Payments
- Go to Payments → Add Payment
- Link payment to invoice
- View outstanding balances on Dashboard

### Update Rates
- Go to Settings
- Update paper/roll rates daily
- All new quotations use updated rates

## Troubleshooting

**Database not created?**
- Make sure you have write permissions
- Check if `hamza_enterprises.db` is created

**PDF not generating?**
- Check if letterhead images exist in `static/images/`
- Check `generated_pdfs/` folder permissions

**Calculations wrong?**
- Verify paper grades and rates in Settings
- Check unit conversion (system uses inches internally)

## Next Steps

1. Add more customers
2. Create multiple quotations
3. Test the complete workflow
4. Set up FBR integration (if needed)
5. Customize company information

## Support

For detailed documentation, see `README.md`
