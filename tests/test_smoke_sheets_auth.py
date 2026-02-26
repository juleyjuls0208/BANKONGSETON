"""
Smoke test: verifies google-auth migration by doing an actual Google Sheets read.
Requires GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEETS_ID env vars to be set.
Skip if not set (CI environment without credentials).
"""
import os
import pytest

CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE')
SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID')

@pytest.mark.skipif(
    not CREDENTIALS_FILE or not SHEETS_ID,
    reason="GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEETS_ID not set — skipping live Sheets test"
)
def test_smoke_sheets_read():
    """Authenticate with Google Sheets using google-auth and perform actual read."""
    import gspread
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    spreadsheet = gc.open_by_key(SHEETS_ID)
    # Get list of sheets — minimal read, doesn't assume any particular sheet name
    sheet_list = spreadsheet.worksheets()
    assert isinstance(sheet_list, list), "Expected list of worksheets"
    assert len(sheet_list) > 0, "Spreadsheet has no sheets"
