#!/usr/bin/env bash
# verify-m005-s03.sh — Contract verification for M005 S03: Backend QR Payment Flow
# Usage: bash scripts/verify-m005-s03.sh
# Must exit 0 for the slice to be considered contractually complete.
set -euo pipefail

echo "[S03 verify] 1/3 Python syntax checks..."
python -m py_compile backend/api/api_server.py && echo "  OK: api_server.py"
python -m py_compile backend/dashboard/web_app.py && echo "  OK: web_app.py"
python -m py_compile backend/dashboard/cashier/cashier_routes.py && echo "  OK: cashier_routes.py"

echo "[S03 verify] 2/3 Endpoint and state grep checks..."
grep -q 'pending_qr_token.*None' backend/dashboard/web_app.py \
    && echo "  OK: app.pending_qr_token initialized in web_app.py"
grep -q 'qr-pending' backend/dashboard/web_app.py \
    && echo "  OK: qr-pending route in web_app.py"
grep -q 'pending_qr_token' backend/dashboard/web_app.py \
    && echo "  OK: pending_qr_token referenced in web_app.py"
grep -q 'qr-generate' backend/dashboard/cashier/cashier_routes.py \
    && echo "  OK: qr-generate route in cashier_routes.py"
grep -q 'pending_qr_token' backend/dashboard/cashier/cashier_routes.py \
    && echo "  OK: pending_qr_token written in cashier_routes.py"
grep -q 'api/qr/' backend/dashboard/web_app.py \
    && echo "  OK: /api/qr/<token> route in web_app.py"
grep -q 'qr/confirm' backend/dashboard/web_app.py \
    && echo "  OK: qr/confirm route in web_app.py"
grep -q 'qr_payment' backend/dashboard/web_app.py \
    && echo "  OK: qr_payment socketio.emit in web_app.py"
grep -q 'qr_payment' backend/dashboard/cashier/templates/cashier_index.html \
    && echo "  OK: socket.on(qr_payment) in cashier_index.html"
grep -q 'SERVER_URL' backend/dashboard/cashier/cashier_routes.py \
    && echo "  OK: SERVER_URL consumed in cashier_routes.py"
grep -q 'jwt_token' backend/api/api_server.py \
    && echo "  OK: jwt_token in api_server.py login response"

echo "[S03 verify] 3/3 Environment documentation checks..."
grep -q 'SERVER_URL' .env.example \
    && echo "  OK: SERVER_URL in .env.example"
grep -q 'SERVER_URL' docs/DEPLOY.md \
    && echo "  OK: SERVER_URL in docs/DEPLOY.md"

echo ""
echo "All S03 checks passed."
