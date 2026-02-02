#!/usr/bin/env python3
"""
Google Sheets Setup Script
Creates the required sheets and column headers
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os

load_dotenv()

def setup_sheets():
    """Create and configure Google Sheets structure"""
    
    print("\n" + "="*50)
    print("GOOGLE SHEETS SETUP")
    print("="*50 + "\n")
    
    try:
        # Connect to Google Sheets
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        sheet_id = os.getenv('GOOGLE_SHEETS_ID')
        if not sheet_id:
            print("✗ GOOGLE_SHEETS_ID not found in .env file")
            print("\nPlease:")
            print("1. Create a new Google Sheet")
            print("2. Copy the Sheet ID from the URL")
            print("3. Add it to .env file as GOOGLE_SHEETS_ID=your_id_here")
            return
        
        spreadsheet = client.open_by_key(sheet_id)
        print(f"✓ Connected to: {spreadsheet.title}")
        
        # Sheet definitions
        sheets_config = {
            'Users': [
                'StudentID', 'Name', 'Grade', 'Section', 
                'IDCardNumber', 'MoneyCardNumber', 'Status', 
                'ParentEmail', 'DateRegistered'
            ],
            'Money Accounts': [
                'MoneyCardNumber', 'LinkedIDCard', 'Balance', 
                'Status', 'LastUpdated', 'TotalLoaded'
            ],
            'Transactions Log': [
                'TransactionID', 'Timestamp', 'StudentID', 
                'MoneyCardNumber', 'TransactionType', 'Amount', 
                'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage'
            ],
            'Lost Card Reports': [
                'ReportID', 'ReportDate', 'StudentID', 
                'OldCardNumber', 'NewCardNumber', 'TransferredBalance', 
                'ReportedBy', 'Status'
            ]
        }
        
        # Create/update each sheet
        for sheet_name, headers in sheets_config.items():
            try:
                # Try to get existing sheet
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"  ✓ Found existing sheet: {sheet_name}")
                
                # Check if headers are already set
                existing_headers = worksheet.row_values(1)
                if existing_headers != headers:
                    worksheet.update('A1', [headers])
                    print(f"    → Updated headers")
                
            except gspread.WorksheetNotFound:
                # Create new sheet
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )
                worksheet.update('A1', [headers])
                print(f"  ✓ Created new sheet: {sheet_name}")
        
        # Delete default "Sheet1" if it exists
        try:
            default_sheet = spreadsheet.worksheet('Sheet1')
            if len(spreadsheet.worksheets()) > 1:
                spreadsheet.del_worksheet(default_sheet)
                print("  ✓ Removed default Sheet1")
        except:
            pass
        
        print("\n✓ Google Sheets setup complete!")
        print(f"\nSpreadsheet URL:")
        print(f"https://docs.google.com/spreadsheets/d/{sheet_id}")
        
    except FileNotFoundError:
        print("✗ credentials.json not found")
        print("\nPlease:")
        print("1. Go to Google Cloud Console")
        print("2. Create a service account")
        print("3. Download the JSON key")
        print("4. Save it as credentials.json in this directory")
        
    except Exception as e:
        print(f"✗ Setup failed: {e}")

if __name__ == '__main__':
    setup_sheets()
