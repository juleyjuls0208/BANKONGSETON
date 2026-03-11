"""
Migration Script: Add ItemsJson column to existing Transactions
Backfills existing transactions with empty ItemsJson field
"""

import gspread
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_transactions():
    """Add ItemsJson column to Transactions Log sheet"""
    try:
        # Setup Google Sheets connection
        credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
        if not os.path.exists(credentials_path):
            credentials_path = 'credentials.json'
        
        client = gspread.service_account(filename=credentials_path)
        db = client.open_by_key(os.getenv('GOOGLE_SHEETS_ID'))
        
        # Get Transactions Log sheet
        trans_sheet = db.worksheet('Transactions Log')
        
        # Get all values
        all_values = trans_sheet.get_all_values()
        
        if not all_values:
            print("❌ No data found in Transactions Log")
            return
        
        headers = all_values[0]
        
        # Check if ItemsJson column already exists
        if 'ItemsJson' in headers:
            print("✅ ItemsJson column already exists")
            return
        
        # Add ItemsJson to headers
        headers.append('ItemsJson')
        trans_sheet.update('A1:Z1', [headers])
        
        print(f"✅ Added 'ItemsJson' column to Transactions Log")
        print(f"📊 Total rows: {len(all_values)}")
        
        # Backfill empty ItemsJson for existing rows (optional - already empty by default)
        num_rows = len(all_values)
        if num_rows > 1:
            print(f"✅ {num_rows - 1} existing transactions will have empty ItemsJson by default")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

def migrate_users_schema():
    """Add ParentEmail, FCMToken, Role columns to Users sheet"""
    try:
        credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
        if not os.path.exists(credentials_path):
            credentials_path = 'credentials.json'
        
        client = gspread.service_account(filename=credentials_path)
        db = client.open_by_key(os.getenv('GOOGLE_SHEETS_ID'))
        
        # Get Users sheet
        users_sheet = db.worksheet('Users')
        
        # Get headers
        all_values = users_sheet.get_all_values()
        if not all_values:
            print("❌ No data found in Users sheet")
            return
        
        headers = all_values[0]
        
        # Add new columns if they don't exist
        columns_to_add = []
        if 'ParentEmail' not in headers:
            columns_to_add.append('ParentEmail')
        if 'FCMToken' not in headers:
            columns_to_add.append('FCMToken')
        if 'Role' not in headers:
            columns_to_add.append('Role')
        
        if columns_to_add:
            headers.extend(columns_to_add)
            users_sheet.update('A1:Z1', [headers])
            print(f"✅ Added columns to Users: {', '.join(columns_to_add)}")
        else:
            print("✅ All required columns already exist in Users sheet")
        
    except Exception as e:
        print(f"❌ Users migration failed: {e}")
        import traceback
        traceback.print_exc()

def create_products_sheet():
    """Create Products sheet if it doesn't exist"""
    try:
        credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
        if not os.path.exists(credentials_path):
            credentials_path = 'credentials.json'
        
        client = gspread.service_account(filename=credentials_path)
        db = client.open_by_key(os.getenv('GOOGLE_SHEETS_ID'))
        
        # Check if Products sheet exists
        try:
            products_sheet = db.worksheet('Products')
            print("✅ Products sheet already exists")
            return
        except:
            pass
        
        # Create Products sheet
        products_sheet = db.add_worksheet(title='Products', rows=100, cols=10)
        
        # Add headers
        headers = ['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']
        products_sheet.update('A1:G1', [headers])
        
        # Load initial products from products.json
        import json
        products_json_path = os.path.join(os.path.dirname(__file__), 'data', 'products.json')
        
        if os.path.exists(products_json_path):
            with open(products_json_path, 'r') as f:
                products = json.load(f)
            
            # Prepare rows
            rows = []
            for product in products:
                rows.append([
                    product['id'],
                    product['name'],
                    product['category'],
                    product['price'],
                    product.get('image_url', ''),
                    'TRUE',  # Active
                    ''  # DateAdded - empty for now
                ])
            
            # Write products to sheet
            if rows:
                products_sheet.update(f'A2:G{len(rows) + 1}', rows)
                print(f"✅ Created Products sheet with {len(rows)} products")
        else:
            print("✅ Created empty Products sheet (products.json not found)")
        
    except Exception as e:
        print(f"❌ Products sheet creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("🔄 Starting Database Migration")
    print("=" * 60)
    
    print("\n1️⃣ Migrating Transactions Log...")
    migrate_transactions()
    
    print("\n2️⃣ Migrating Users schema...")
    migrate_users_schema()
    
    print("\n3️⃣ Creating Products sheet...")
    create_products_sheet()
    
    print("\n" + "=" * 60)
    print("✅ Migration Complete")
    print("=" * 60)
