# Bangko ng Seton - Android Mobile App

Mobile application for students and parents to view balance, transactions, and attendance records.

## Features

### 📱 Student/Parent App Features
- **Home Dashboard**
  - View current balance
  - Student information display
  - Quick action buttons
  
- **Transaction History**
  - View all purchase transactions
  - See balance after each transaction
  - Filter by date range
  
- **Attendance Records**
  - View daily attendance logs
  - Check-in times
  - Attendance status
  
- **Profile Management**
  - View student details
  - Card numbers (ID & Money)
  - Account status
  - Parent email

## Technology Stack

- **Language**: Kotlin
- **Min SDK**: 24 (Android 7.0)
- **Target SDK**: 36
- **Architecture**: Fragment-based navigation with BottomNavigationView
- **Backend**: Google Sheets API
- **UI Components**: Material Design 3

## Project Structure

```
app/
├── src/main/java/com/juls/bankongsetonandroid/
│   ├── MainActivity.kt            # Main activity with navigation
│   ├── HomeFragment.kt            # Balance and overview
│   ├── TransactionsFragment.kt    # Transaction history
│   ├── AttendanceFragment.kt      # Attendance records
│   ├── ProfileFragment.kt         # Student profile
│   ├── Transaction.kt             # Transaction data class
│   ├── Attendance.kt              # Attendance data class
│   ├── TransactionAdapter.kt      # RecyclerView adapter
│   ├── AttendanceAdapter.kt       # RecyclerView adapter
│   └── SheetsHelper.kt            # Google Sheets API helper
├── res/
│   ├── layout/                    # XML layouts
│   ├── menu/                      # Bottom navigation menu
│   ├── drawable/                  # Icons and drawables
│   └── values/                    # Colors, strings, themes
└── AndroidManifest.xml
```

## Setup Instructions

### Prerequisites
1. Android Studio (latest version)
2. JDK 11 or higher
3. Android SDK 24+
4. Google Sheets API credentials

### Installation

1. **Open Project in Android Studio**
   ```bash
   cd ANDROID
   # Open folder in Android Studio
   ```

2. **Configure Google Sheets API**
   - Get credentials from Google Cloud Console
   - Update `SPREADSHEET_ID` in `SheetsHelper.java`
   - Add `credentials.json` to `app/src/main/assets/`

3. **Update Dependencies**
   ```bash
   # Sync Gradle files in Android Studio
   File > Sync Project with Gradle Files
   ```

4. **Build and Run**
   ```bash
   # Connect Android device or start emulator
   # Click Run button or press Shift+F10
   ```

## Configuration

### Google Sheets Integration

1. **Enable Google Sheets API**
   - Go to Google Cloud Console
   - Enable Sheets API for your project
   - Create service account credentials

2. **Update Spreadsheet ID**
   ```java
   // In SheetsHelper.java
   private static final String SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE";
   ```

3. **Sheet Structure Expected**
   - **Users**: StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered
   - **Money Accounts**: MoneyCardNumber, IDCardNumber, Balance, Status, LastUpdated, TotalLoaded
   - **Transactions**: Timestamp, MoneyCardNumber, IDCardNumber, Type, Amount, Balance
   - **Attendance**: Date, Time, IDCardNumber, Status

## API Integration

### SheetsHelper Methods

```java
// Get user data by ID card
List<List<Object>> getUserData(String idCardNumber)

// Get transaction history
List<Transaction> getTransactions(String moneyCardNumber)

// Get attendance records
List<Attendance> getAttendance(String idCardNumber)

// Get current balance
double getBalance(String moneyCardNumber)
```

## UI Screens

### 1. Home Screen
- Displays student name and ID
- Shows current balance in large card
- Quick action buttons for Transactions and Attendance

### 2. Transactions Screen
- RecyclerView list of all transactions
- Shows type, amount, timestamp, and resulting balance
- Color-coded amounts (red for deductions)

### 3. Attendance Screen
- RecyclerView list of attendance records
- Shows date, time, and status
- Status badge (Present/Absent)

### 4. Profile Screen
- Student personal information
- ID card and money card numbers
- Account status indicator
- Parent email

## Dependencies

```gradle
// Core Android
androidx.appcompat:appcompat
androidx.constraintlayout
com.google.android.material:material

// UI Components
androidx.cardview:cardview
androidx.recyclerview:recyclerview

// Google Sheets API
google-api-client-android
google-api-services-sheets
google-http-client-gson

// Network
retrofit2
okhttp3
```

## Development Notes

### TODO List
- [ ] Implement Google Sheets authentication
- [ ] Add pull-to-refresh functionality
- [ ] Add offline mode with local caching
- [ ] Implement push notifications
- [ ] Add search/filter in transactions
- [ ] Add date range picker for attendance
- [ ] Implement remote balance loading
- [ ] Add spending analytics charts
- [ ] Add password/PIN protection
- [ ] Multi-student support for parents

### Known Issues
- Google Sheets API initialization not yet implemented
- Credentials.json needs to be added to project
- No error handling for network failures
- No loading indicators

## Testing

### Manual Testing Checklist
- [ ] App launches successfully
- [ ] Bottom navigation switches between fragments
- [ ] Home screen displays placeholder data
- [ ] Transaction list renders correctly
- [ ] Attendance list renders correctly
- [ ] Profile displays all fields
- [ ] App handles screen rotation

### API Testing
Once Google Sheets is connected:
- [ ] Verify user data loads
- [ ] Check transaction list accuracy
- [ ] Confirm attendance records
- [ ] Validate balance updates

## Deployment

### Generate APK
```bash
# In Android Studio
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

### Generate Signed APK
```bash
# Create keystore
Build > Generate Signed Bundle / APK
# Follow wizard to create release APK
```

## Support & Contribution

For issues or feature requests, contact the development team.

## License

Copyright © 2024 Bangko ng Seton Project
```

This Android app integrates with the existing Google Sheets backend to provide students and parents with mobile access to:
- Real-time balance information
- Complete transaction history
- Attendance tracking
- Profile management

The app is built with Material Design and follows Android development best practices.
