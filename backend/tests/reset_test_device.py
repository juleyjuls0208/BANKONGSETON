"""One-off cleanup: clear the device binding for TEST66F5 so it is not stuck to
the test phone. Keeps the PIN. Run on the VM only."""
import sys
sys.path.insert(0, "/opt/bankongseton/backend/api")
import api_server as a

SID = "TEST66F5"
db = a.get_sheets_client()
ws = db.worksheet("student_auth")
rows = ws.get_all_records()
for idx, r in enumerate(rows, start=2):
    if str(r.get("StudentID", "")).strip() == SID:
        now = a.get_philippines_time().strftime("%Y-%m-%d %H:%M:%S")
        ws.update("A{0}:D{0}".format(idx), [[SID, str(r.get("PinHash", "")), "", now]])
        print("reset device binding for", SID, "(PIN kept). row", idx)
        break
else:
    print(SID, "not found in student_auth")
