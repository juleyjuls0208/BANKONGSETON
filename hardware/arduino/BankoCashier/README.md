# Bangko Cashier Station

## Purpose
This Arduino handles payment transactions at the cashier/canteen.

## Upload Instructions
1. Open Arduino IDE
2. File → Open → Select `BankoCashier.ino`
3. Select Board: Arduino UNO
4. Select Port: Your Arduino's COM port
5. Click Upload

## Hardware Requirements
- Arduino UNO R3
- RFID RC522 Module (3.3V!)
- 16x2 LCD with I2C
- Piezo Buzzer
- Same pin configuration as admin station

## Usage
1. Upload this sketch to Arduino
2. Connect Arduino to PC via USB
3. Run `python bangko_backend.py` on the PC
4. Students can now make payments

## Payment Workflow
1. Student taps Money Card
2. LCD shows balance
3. Student taps ID Card  
4. Payment processed
5. Attendance logged automatically

## Serial Protocol
**Arduino sends:**
- `<CHECK|MONEYCARD_UID>` - Check balance
- `<VERIFY|MONEYCARD_UID|IDCARD_UID>` - Process payment

**Python responds:**
- `<BALANCE|amount>` - Balance amount
- `<SUCCESS|name|amount|newbalance>` - Payment success
- `<ERROR|message>` - Error occurred

## Troubleshooting
- **No card reading**: Check RFID wiring (must be 3.3V!)
- **LCD blank**: Adjust I2C address (0x27 or 0x3F)
- **No Python response**: Check COM port, restart backend
