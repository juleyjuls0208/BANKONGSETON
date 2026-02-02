# Email Notification Setup Guide

## Overview

Bangko ng Seton sends email notifications to parents when:
- Balance is loaded (top-up confirmation)
- Balance is low (below ₱50)
- Large transaction occurs (≥₱100)

## Quick Setup (Gmail)

### Step 1: Generate Gmail App Password

1. **Go to Google Account Security**
   - Visit: https://myaccount.google.com/security
   - Or go to your Google Account → Security

2. **Enable 2-Step Verification** (if not already enabled)
   - Scroll to "How you sign in to Google"
   - Click "2-Step Verification" → Follow setup

3. **Create App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Or search "App passwords" in your Google Account
   - Select:
     - App: "Mail"
     - Device: "Windows Computer" (or custom name)
   - Click **Generate**
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 2: Update `.env` File

Open `.env` and replace these values:

```env
# Email Notifications (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-school-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
FROM_EMAIL=your-school-email@gmail.com
```

**Replace:**
- `your-school-email@gmail.com` → Your actual Gmail address
- `abcdefghijklmnop` → The 16-character app password (remove spaces)

### Step 3: Restart Server

If the dashboard is running, restart it:
```bash
# Stop current server (Ctrl+C)
# Start again
python backend/dashboard/admin_dashboard.py
```

### Step 4: Test Email

1. Go to dashboard
2. Load money to a student with a valid parent email
3. Check parent's inbox (may be in Spam folder first time)

## Parent Email Requirement

For parents to receive emails, the **Users** Google Sheet must have:
- Column name: `ParentEmail`
- Valid email addresses (e.g., `parent@gmail.com`)

## Alternative Providers

### Outlook/Hotmail

```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-outlook-password
FROM_EMAIL=your-email@outlook.com
```

### SendGrid (Professional)

1. Sign up: https://sendgrid.com (free up to 100 emails/day)
2. Create API key
3. Configure:

```env
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=verified-sender@yourdomain.com
```

### School Email Server

Contact your school IT admin for:
- SMTP server address
- Port (usually 587 or 465)
- Username and password

## Troubleshooting

### Emails not sending?

**Check 1: Verify configuration**
```python
# Test in Python
from backend.notifications import get_notification_manager
nm = get_notification_manager()
print(f"Email enabled: {nm.email_notifier.enabled}")
print(f"SMTP Server: {nm.email_notifier.smtp_server}")
```

**Check 2: Test email directly**
```python
from backend.notifications import EmailNotifier
notifier = EmailNotifier()
notifier.send_email(
    to_email="test@gmail.com",
    subject="Test Email",
    body="This is a test"
)
```

**Check 3: Gmail issues**
- ✅ 2-Step Verification enabled?
- ✅ App password (not regular password)?
- ✅ "Less secure app access" disabled? (not needed with app password)
- ✅ Removed spaces from app password?

**Check 4: Check logs**
- Look for `[Email]` or `[Email Error]` messages in console
- Check if it says "Would send to..." (means disabled)

### Gmail Rate Limits

- **Free Gmail:** ~500 emails/day
- **Google Workspace:** 2,000 emails/day
- If exceeded, emails will fail for 24 hours

### Email goes to Spam

First email often lands in spam. Ask parents to:
1. Check Spam folder
2. Mark email as "Not Spam"
3. Add sender to contacts

## Security Notes

⚠️ **Never commit `.env` to git!**
- `.env` is in `.gitignore` for security
- App passwords give full email access
- Rotate passwords if exposed

✅ **Best practices:**
- Use dedicated email for school notifications
- Use app-specific password (not main password)
- Monitor sent emails regularly
- Consider SendGrid for production (better logging)

## Email Templates

All emails include:
- Professional HTML styling
- School branding (Bangko ng Seton)
- Transaction details
- Philippine timezone timestamps
- Plain text fallback (for old email clients)

### Load Confirmation Email
```
Subject: Balance Loaded - Juan Dela Cruz

Amount Loaded: ₱500.00
New Balance: ₱1,250.00
Date/Time: 2026-02-02 23:10:15
```

### Low Balance Alert
```
Subject: Low Balance Alert - Juan Dela Cruz

Current Balance: ₱35.00

Please load more funds to ensure your child can continue 
making purchases at school.
```

### Large Transaction Alert
```
Subject: Large Transaction Alert - Juan Dela Cruz

Amount: ₱150.00
Type: Purchase
Date/Time: 2026-02-02 14:30:00

If you did not authorize this, contact Finance Office.
```

## Support

For issues:
1. Check logs for error messages
2. Test SMTP credentials with online tools
3. Contact school IT for server-based email
4. Consider SendGrid for professional needs
