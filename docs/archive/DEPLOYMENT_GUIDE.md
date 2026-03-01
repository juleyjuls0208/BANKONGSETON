# Deployment Guide - Bangko ng Seton

## 🔒 Security Checklist

Before deploying, ensure you've completed these steps:

### 1. Environment Variables Setup

1. **Copy example file:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` and set secure values:**
   - `GOOGLE_SHEETS_ID` - Your Google Sheets database ID
   - `FLASK_SECRET_KEY` - Generate a strong random key (min 32 characters)
   - `ADMIN_USERNAME` - Change from default 'admin'
   - `ADMIN_PASSWORD` - Set a strong password (min 12 characters)

3. **Generate secure secret key (Python):**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

### 2. Google Sheets Credentials

1. **Copy example file:**
   ```bash
   copy credentials.json.example credentials.json
   ```

2. **Get Google Service Account credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Sheets API
   - Create Service Account
   - Download JSON key file
   - Replace `credentials.json` with your key file

3. **Share Google Sheet:**
   - Open your Google Sheet
   - Click Share
   - Add service account email (from credentials.json)
   - Give "Editor" permissions

### 3. Verify .gitignore

Ensure these files are **NEVER** committed:
- ✅ `.env` - Contains passwords and secrets
- ✅ `credentials.json` - Contains Google API keys
- ✅ `*.log` - May contain sensitive data

### 4. Security Recommendations

**For Production Deployment:**

1. **Use HTTPS:**
   - Deploy behind reverse proxy (nginx, Apache)
   - Use Let's Encrypt for free SSL certificates

2. **Change Default Ports:**
   ```python
   # In admin_dashboard.py, change from:
   app.run(host='0.0.0.0', port=5002)
   # To production server like:
   # gunicorn -w 4 -b 0.0.0.0:8000 admin_dashboard:app
   ```

3. **Enable Rate Limiting:**
   ```bash
   pip install flask-limiter
   ```

4. **Set Strong Passwords:**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Never use default passwords in production

5. **Firewall Rules:**
   - Only allow necessary ports (443 for HTTPS)
   - Block direct access to Python port
   - Use reverse proxy for external access

6. **Regular Backups:**
   - Backup Google Sheets regularly
   - Export transaction logs
   - Keep offline copies

## 📦 Installation on New Server

### Prerequisites
- Python 3.8 or higher
- Arduino connected to COM port
- Google Service Account with Sheets API access

### Setup Steps

1. **Clone repository:**
   ```bash
   git clone <your-repo-url>
   cd BANKONGSETON
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   copy .env.example .env
   copy credentials.json.example credentials.json
   # Edit both files with your values
   ```

5. **Initialize Google Sheets:**
   ```bash
   python setup_sheets.py
   ```

6. **Start admin dashboard:**
   ```bash
   python admin_dashboard.py
   ```

## 🚀 Production Deployment

### Option 1: Local Server

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 admin_dashboard:app
```

### Option 2: Cloud Deployment (Heroku/Railway)

1. **Add Procfile:**
   ```
   web: gunicorn admin_dashboard:app
   ```

2. **Set environment variables in platform:**
   - Don't commit `.env` to git
   - Set all variables in platform dashboard

3. **Note: Arduino features won't work in cloud**
   - Card reader requires physical USB connection
   - Deploy backend separately on local hardware
   - Use cloud only for data viewing/management

## 🔧 Troubleshooting

### Common Issues

1. **"Card reader not connected"**
   - Check Arduino USB cable
   - Verify COM port in `.env`
   - Run as Administrator (Windows)

2. **"Google Sheets API error"**
   - Check credentials.json is valid
   - Verify service account has Sheet access
   - Enable Google Sheets API in Cloud Console

3. **"Invalid login credentials"**
   - Check ADMIN_USERNAME and ADMIN_PASSWORD in `.env`
   - Restart server after changing `.env`

## 📞 Support

For issues or questions:
1. Check error logs in terminal
2. Review this guide
3. Check Google Sheets API quotas
4. Verify all environment variables are set

## ⚠️ IMPORTANT SECURITY WARNINGS

**NEVER commit these files to git:**
- `.env`
- `credentials.json`
- `*.log` files
- Any file containing passwords or API keys

**Before pushing to GitHub:**
1. Run: `git status`
2. Verify no sensitive files are staged
3. Check `.gitignore` is working
4. Review commit with: `git diff --cached`

**If you accidentally committed secrets:**
1. Rotate all credentials immediately
2. Generate new Google Service Account
3. Change all passwords
4. Use `git filter-branch` to remove from history
5. Force push to overwrite history

---

**Remember:** Security is not a one-time setup. Regularly review access logs, update passwords, and keep dependencies updated.
