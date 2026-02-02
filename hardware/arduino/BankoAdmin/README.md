# Bangko Admin Station

## Purpose
This Arduino handles card registration and balance loading in the admin office.

## Upload Instructions
1. Open Arduino IDE
2. File → Open → Select `BankoAdmin.ino`
3. Select Board: Arduino UNO
4. Select Port: Your Arduino's COM port
5. Click Upload

## Hardware Requirements
- Arduino UNO R3
- RFID RC522 Module (3.3V!)
- 16x2 LCD with I2C
- Piezo Buzzer
- Same pin configuration as cashier station

## Usage
1. Upload this sketch to Arduino
2. Connect Arduino to PC via USB
3. Run `python card_manager.py` on the PC
4. Follow menu prompts

## Registration Workflows

### Register Student:
1. Enter student details in Python
2. Tap ID card when prompted
3. Student registered!

### Link Money Card:
1. Select option 2 in Python menu
2. **Tap Student ID card first** (identifies student)
3. **Tap Money card second** (links to student)
4. Enter initial balance
5. Cards linked!

### Load Balance:
1. Select option 3 in Python menu
2. Tap Money card
3. Enter amount to load
4. Balance updated!

## Serial Protocol
**Arduino sends:**
- `<CARD|UID>` - Card was tapped

**Python sends:**
- `<DISPLAY|line1|line2>` - Update LCD display
- `<SUCCESS|message>` - Show success with beep
- `<ERROR|message>` - Show error with beep
- `<CLEAR|>` - Clear display to idle

## Troubleshooting
- **Cards reading multiple times**: Normal, debounce is 2 seconds
- **No card reading**: Check RFID wiring (must be 3.3V!)
- **LCD blank**: Adjust I2C address (0x27 or 0x3F)
- **Python not receiving**: Check COM port in .env
