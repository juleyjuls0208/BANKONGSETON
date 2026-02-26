"""
Migration Script: Add ItemsJson column to existing Transactions
Backfills existing transactions with empty ItemsJson field
"""

import gspread
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
try:
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

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
            logger.warning("event=migrate_transactions_empty sheet=Transactions Log")
            return
        
        headers = all_values[0]
        
        # Check if ItemsJson column already exists
        if 'ItemsJson' in headers:
            logger.info("event=migrate_transactions_skip reason=column_exists column=ItemsJson")
            return
        
        # Add ItemsJson to headers
        headers.append('ItemsJson')
        trans_sheet.update('A1:Z1', [headers])
        
        logger.info("event=migrate_transactions_column_added column=ItemsJson")
        logger.info("event=migrate_transactions_rows total=%d", len(all_values))
        
        # Backfill empty ItemsJson for existing rows (optional - already empty by default)
        num_rows = len(all_values)
        if num_rows > 1:
            logger.info("event=migrate_transactions_backfill rows=%d", num_rows - 1)
        
    except Exception as e:
        logger.error("event=migrate_transactions_failed error=%s", e, exc_info=True)

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
            logger.warning("event=migrate_users_empty sheet=Users")
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
            logger.info("event=migrate_users_columns_added columns=%s", ', '.join(columns_to_add))
        else:
            logger.info("event=migrate_users_skip reason=all_columns_exist")
        
    except Exception as e:
        logger.error("event=migrate_users_failed error=%s", e, exc_info=True)

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
            logger.info("event=create_products_sheet_skip reason=already_exists")
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
                logger.info("event=create_products_sheet_done count=%d", len(rows))
        else:
            logger.info("event=create_products_sheet_empty reason=products_json_not_found")
        
    except Exception as e:
        logger.error("event=create_products_sheet_failed error=%s", e, exc_info=True)

if __name__ == '__main__':
    logger.info("event=migration_start")
    
    logger.info("event=migration_step step=1 name=transactions_log")
    migrate_transactions()
    
    logger.info("event=migration_step step=2 name=users_schema")
    migrate_users_schema()
    
    logger.info("event=migration_step step=3 name=products_sheet")
    create_products_sheet()
    
    logger.info("event=migration_complete")
