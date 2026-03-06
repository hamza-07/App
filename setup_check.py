"""
Quick setup verification script
Run this to check if everything is set up correctly
"""

import os
import sys

def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        'flask',
        'flask_sqlalchemy',
        'flask_migrate',
        'reportlab',
        'Pillow',
        'qrcode',
        'requests'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nRun: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies installed")
        return True

def check_folders():
    """Check if required folders exist"""
    folders = [
        'static/images',
        'templates',
        'templates/customers',
        'templates/quotations',
        'templates/challans',
        'templates/invoices',
        'templates/payments',
        'utils',
        'generated_pdfs'
    ]
    
    missing = []
    for folder in folders:
        if not os.path.exists(folder):
            missing.append(folder)
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Created folder: {folder}")
    
    if not missing:
        print("✅ All folders exist")
    return True

def check_letterheads():
    """Check if letterhead images exist"""
    letterheads = [
        'static/images/Latterhead.png',
        'static/images/Latterhead1.png'
    ]
    
    missing = []
    for letterhead in letterheads:
        if not os.path.exists(letterhead):
            missing.append(letterhead)
    
    if missing:
        print("⚠️  Letterhead images not found:")
        for img in missing:
            print(f"   - {img}")
        print("\nPlease add your company letterhead images to static/images/")
        return False
    else:
        print("✅ Letterhead images found")
        return True

def main():
    print("=" * 50)
    print("Hamza Enterprises - Setup Verification")
    print("=" * 50)
    print()
    
    deps_ok = check_dependencies()
    print()
    
    folders_ok = check_folders()
    print()
    
    letterheads_ok = check_letterheads()
    print()
    
    print("=" * 50)
    if deps_ok and folders_ok:
        if letterheads_ok:
            print("✅ Setup complete! You can run: python app.py")
        else:
            print("⚠️  Setup almost complete. Add letterhead images and run: python app.py")
    else:
        print("❌ Please fix the issues above before running the application")
    print("=" * 50)

if __name__ == '__main__':
    main()
