# Bangko ng Seton - Unified Dashboard

## Overview

The Finance Dashboard has been merged with Admin Dashboard to create a unified web application with role-based access control.

## Login Credentials

### Finance User
```
Username: financedashboard
Password: finance2025
Role: Finance
```

**Permissions:**
- ✅ View dashboard statistics
- ✅ View/search students
- ✅ View transactions
- ✅ Load money to student accounts
- ❌ Cannot access card management (admin only)

### Admin User
```
Username: admindashboard
Password: admin2025
Role: Admin
```

**Permissions:**
- ✅ Everything Finance can do
- ✅ **Card Management (Admin Only):**
  - Connect Arduino
  - Register students with ID cards
  - Link money cards to students
  - Report lost cards
  - Replace lost cards

## Features

### For All Users (Finance + Admin)

#### Dashboard
- View total students count
- View today's transactions count
- Search students by name or ID
- View recent activity
- Load balance to student accounts

#### Students Page
- View all registered students
- Search and filter
- View student details
- Load money to accounts

#### Transactions Page
- View all transactions
- Filter by date, student, type
- Export transaction history

### Admin-Only Features

#### Card Management Section
The entire card management section is only visible to admin users. Finance users will not see this section at all.

**Arduino Connection:**
- Connect to Arduino via serial port
- Real-time status monitoring
- Card reading functionality

**Student Registration:**
1. **Register New Student**
   - Tap ID card on reader
   - Fill in student details (ID, Name, Email)
   - Student is registered in system

2. **Link Money Card**
   - Search for student without money card
   - Tap money card on reader
   - Card is linked to student account
   - Account created with ₱0 balance

**Lost Card Management:**
1. **Report Lost Card**
   - Search for student with active card
   - Report card as lost
   - Old card is deactivated
   - Balance is preserved
   - Lost card report created

2. **Replace Lost Card**
   - View students with pending lost card reports
   - Tap new money card on reader
   - Balance transferred from old card
   - New card activated
   - Student can use new card immediately

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
FINANCE_USERNAME=financedashboard
FINANCE_PASSWORD=finance2025
ADMIN_USERNAME=admin
ADMIN_PASSWORD=bangko2025
```

3. Run the dashboard:
```bash
python admin_dashboard.py
```

4. Open browser to `http://localhost:5003`

## Google Sheets Setup

Required sheets:
- **Users** - Student information
- **Money Accounts** - Balance and card information
- **Transactions** - Transaction history
- **Lost Card Reports** - Lost card tracking

Run `python setup_sheets.py` to create the "Lost Card Reports" sheet if it doesn't exist.

## Security Features

### Lost Card Protection
- Students with lost cards cannot log in to mobile app
- Active sessions are immediately invalidated when card is reported lost
- Lost cards cannot be used for transactions
- Balance is preserved and transferred to new card

### Role-Based Access
- Finance users have limited permissions (viewing and loading only)
- Admin users have full access including card management
- Session-based authentication
- Secure credential storage via environment variables

## Deployment

For production deployment:
1. Set `debug=False` in `admin_dashboard.py`
2. Use production WSGI server (e.g., Gunicorn)
3. Set strong passwords in environment variables
4. Enable HTTPS
5. Configure firewall rules

See `DEPLOYMENT.md` for detailed instructions.

## Troubleshooting

### Arduino Not Connecting
- Check COM port is correct
- Ensure Arduino is powered on
- Verify serial connection settings (115200 baud)
- Try disconnecting and reconnecting

### Card Reading Timeout
- Ensure card is placed firmly on reader
- Check reader is powered and connected
- Verify Arduino sketch is running correctly
- Try reading card again

### Login Issues
- Verify credentials match environment variables
- Check session is not expired
- Clear browser cookies and try again

## Support

For issues or questions, refer to:
- `ARCHITECTURE.md` - System architecture
- `SECURITY.md` - Security features
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
