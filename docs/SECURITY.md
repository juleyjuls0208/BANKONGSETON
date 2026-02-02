# Security Policy - Bangko ng Seton

## 🔒 Security Best Practices

### Implemented Security Features

1. **Authentication & Authorization**
   - Session-based authentication for admin dashboard
   - Login required for all admin endpoints
   - Automatic session timeout

2. **Data Protection**
   - Environment variables for sensitive configuration
   - Google Service Account for API access
   - No hardcoded credentials in source code

3. **Input Validation**
   - Card UID normalization
   - Transaction amount validation
   - Student ID verification

4. **Secure Communication**
   - HTTPS recommended for production
   - CORS enabled with proper configuration
   - Session cookie security

### Known Limitations

1. **Card Reader Security**
   - Physical access to Arduino required
   - No encryption on serial communication
   - Trust-based system for card reading

2. **Admin Dashboard**
   - Single admin account (can be extended)
   - Basic password authentication
   - No 2FA (recommended to add)

3. **Google Sheets Backend**
   - Service account has full sheet access
   - No row-level security
   - API rate limits apply

## 🚨 Security Checklist for Deployment

### Before Deploying to Production

- [ ] Change `FLASK_SECRET_KEY` to strong random value
- [ ] Change `ADMIN_PASSWORD` from default
- [ ] Change `ADMIN_USERNAME` from default 'admin'
- [ ] Use HTTPS (SSL/TLS certificate)
- [ ] Enable firewall rules
- [ ] Set up regular backups
- [ ] Review `.gitignore` to ensure no secrets committed
- [ ] Generate new Google Service Account credentials
- [ ] Test with non-production data first
- [ ] Set up monitoring and alerts
- [ ] Limit Google Sheets API access to specific IPs (if possible)
- [ ] Document admin access procedures
- [ ] Create incident response plan

### Recommended Enhancements

1. **Two-Factor Authentication (2FA)**
   ```bash
   pip install pyotp qrcode
   ```

2. **Rate Limiting**
   ```bash
   pip install flask-limiter
   ```

3. **Audit Logging**
   - Log all admin actions
   - Track transaction modifications
   - Monitor failed login attempts

4. **Database Encryption**
   - Encrypt sensitive fields in Google Sheets
   - Use field-level encryption for card numbers

5. **API Key Rotation**
   - Rotate Google Service Account keys quarterly
   - Update Flask secret key periodically

## 🔐 Password Requirements

**Production Environment:**
- Minimum 12 characters
- Must include:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Numbers (0-9)
  - Special characters (!@#$%^&*)
- No common passwords
- No personal information

**Generate Strong Password:**
```python
import secrets
import string

def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

print(generate_password())
```

## 🛡️ Incident Response

### If Credentials Are Compromised

1. **Immediate Actions:**
   - Change all passwords immediately
   - Revoke Google Service Account access
   - Generate new credentials.json
   - Update FLASK_SECRET_KEY
   - Check Google Sheets for unauthorized changes
   - Review transaction logs for anomalies

2. **Investigation:**
   - Check server logs for suspicious activity
   - Review recent admin logins
   - Verify transaction history
   - Check for data exports

3. **Recovery:**
   - Restore from backup if data modified
   - Update all credentials
   - Notify users if necessary
   - Document incident

### If Code Repository Is Compromised

1. **If secrets were committed to git:**
   ```bash
   # Remove file from git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push to overwrite history
   git push origin --force --all
   ```

2. **Rotate all credentials:**
   - Generate new Google Service Account
   - Change all passwords
   - Update environment variables
   - Deploy new credentials

## 📊 Monitoring & Alerts

### Recommended Monitoring

1. **Application Monitoring:**
   - Failed login attempts
   - Unusual transaction patterns
   - API error rates
   - Response times

2. **System Monitoring:**
   - CPU/Memory usage
   - Disk space
   - Network traffic
   - Process uptime

3. **Security Monitoring:**
   - Unauthorized access attempts
   - Configuration changes
   - Unusual API calls
   - Sheet access patterns

### Alert Thresholds

- **Critical:** Failed login attempts > 10 in 5 minutes
- **Warning:** Transaction amount > MAX_TRANSACTION_AMOUNT
- **Info:** New admin login from different location

## 🔍 Security Audit Checklist

**Monthly Review:**
- [ ] Review access logs
- [ ] Check for failed login attempts
- [ ] Verify backup integrity
- [ ] Update dependencies
- [ ] Review transaction patterns
- [ ] Check Google Sheets activity log

**Quarterly Review:**
- [ ] Rotate API credentials
- [ ] Update passwords
- [ ] Security vulnerability scan
- [ ] Review access permissions
- [ ] Update documentation
- [ ] Test disaster recovery

**Annual Review:**
- [ ] Full security audit
- [ ] Penetration testing
- [ ] Review security policies
- [ ] Update incident response plan
- [ ] Staff security training

## 📞 Reporting Security Issues

**If you discover a security vulnerability:**

1. **DO NOT** create a public GitHub issue
2. Email security details to: [Your security contact email]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

4. **Response Time:**
   - Acknowledgment within 24 hours
   - Initial assessment within 72 hours
   - Fix deployed based on severity

## ⚖️ Compliance

### Data Privacy

- Student data stored in Google Sheets
- Service account has minimal required permissions
- No personal data transmitted over HTTP
- Transaction history retained for audit

### Access Control

- Only authorized administrators have dashboard access
- Google Sheet access controlled by service account
- Physical Arduino access required for card operations
- Session-based authentication with timeout

### Data Retention

- Transaction logs retained indefinitely
- No automatic data deletion
- Manual backup recommended monthly
- Export capabilities for compliance

---

**Last Updated:** 2026-02-01

**Version:** 1.0

**Contact:** [Your contact information]
