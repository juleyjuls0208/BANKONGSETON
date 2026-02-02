# 🏦 BANGKO NG SETON - Setup Guide

## 📋 Two Deployment Options

### **Option 1: Local PC (Full Arduino Features)** ✅ RECOMMENDED FOR CARD MANAGEMENT

**What it does:**
- ✅ Full Arduino card reader support
- ✅ Register new students with RFID cards
- ✅ Link money cards to students
- ✅ Report and replace lost cards
- ✅ Load money onto cards
- ✅ View all data (students, transactions, balances)

**How to start:**
```
1. Connect Arduino to USB port
2. Double-click: start_local_dashboard.bat
3. Open browser: http://localhost:5000
```

**Login:**
- **Admin:** `admindashboard` / `admin2025`
- **Finance:** `financedashboard` / `finance2025`

---

### **Option 2: Cloud (PythonAnywhere) - View Only** 🌐

**What it does:**
- ✅ View students and balances
- ✅ View transaction history
- ✅ View reports
- ✅ Access from anywhere with internet
- ❌ NO Arduino features (card reading/management)

**How to access:**
```
Open browser: https://bankoseton.pythonanywhere.com
```

**Login:** Same credentials as local

---

## 🔧 Which One Should You Use?

| Task | Use This |
|------|----------|
| Register new student with card | 💻 **Local PC** |
| Link money card to student | 💻 **Local PC** |
| Report lost card | 💻 **Local PC** |
| Replace lost card | 💻 **Local PC** |
| Load money onto card | 💻 **Local PC** |
| Check balances from home | 🌐 **Cloud** |
| View transactions from phone | 🌐 **Cloud** |
| Check reports remotely | 🌐 **Cloud** |

---

## 📁 File Structure

```
BANKONGSETON/
├── start_local_dashboard.bat    ← START THIS for Arduino features
├── start_arduino_bridge.bat     ← Optional: Forward Arduino to cloud
│
├── FinanceDashboard/
│   ├── admin_dashboard.py       ← Full local version (with Arduino)
│   ├── web_app_complete.py      ← Cloud version (no Arduino)
│   ├── credentials.json         ← Google Sheets credentials
│   ├── .env                     ← Configuration
│   └── templates/               ← HTML files
│
├── ANDROID/                     ← Student mobile app
└── API/                         ← API server for mobile app
```

---

## 🚀 Quick Start (Local)

### First Time Setup:

1. **Install Python packages:**
   ```bash
   cd FinanceDashboard
   pip install -r requirements.txt
   ```

2. **Connect Arduino:**
   - Plug Arduino Uno R3 into USB
   - Make sure RFID reader (RC522) is connected
   - Upload Arduino sketch (if not done)

3. **Start dashboard:**
   ```bash
   start_local_dashboard.bat
   ```

4. **Login:**
   - Open: http://localhost:5000
   - Username: `admindashboard`
   - Password: `admin2025`

---

## 🛠️ Troubleshooting

### "Arduino not found"
- Check USB connection
- Try different USB port
- Check Device Manager (should show COM3 or similar)

### "Port already in use"
- Another program is using port 5000
- Close other Python/Flask apps
- Or change port in `.env` file

### "credentials.json not found"
- Make sure file exists in FinanceDashboard folder
- Download from Google Cloud Console if missing

### "No module named 'serial'"
- Install: `pip install pyserial`

---

## 📊 Google Sheets Setup

Your database uses Google Sheets with these tabs:
- **Users** - Student information
- **Money Accounts** - Card balances
- **Transactions Log** - All transactions
- **Lost Card Reports** - Lost card records

Sheet ID: `1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0`

---

## 🔐 Security

**IMPORTANT:** Never share these files publicly:
- ❌ `credentials.json` (Google API keys)
- ❌ `.env` (passwords and secrets)

---

## 📞 Support

For issues:
1. Check error logs in terminal
2. Verify Arduino is connected
3. Ensure Google Sheets is accessible
4. Check internet connection

---

## 🎯 Summary

**For daily card operations → Use LOCAL (start_local_dashboard.bat)**
**For viewing from anywhere → Use CLOUD (pythonanywhere.com)**

Both use the same Google Sheets database, so data syncs automatically! ✨
