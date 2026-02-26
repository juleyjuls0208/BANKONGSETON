"""
Arduino RC522 Bridge with Timeout Support
Handles card reading with configurable timeout for cashier transactions
"""

import sys
import os
import time
import threading
from flask_socketio import emit

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class ArduinoBridge:
    def __init__(self, arduino_serial, socketio):
        self.arduino = arduino_serial
        self.socketio = socketio
        self.reading_active = False
        self.current_callback = None
        self.timeout_seconds = 5
    
    def read_card_with_timeout(self, callback, timeout=5):
        """
        Read card with timeout
        callback: function(card_uid) called on success
        timeout: seconds to wait before timeout
        """
        if not self.arduino or not self.arduino.is_open:
            self.socketio.emit('card_error', {'message': 'Arduino not connected'})
            return False
        
        self.reading_active = True
        self.current_callback = callback
        self.timeout_seconds = timeout
        
        thread = threading.Thread(target=self._read_card_thread)
        thread.daemon = True
        thread.start()
        
        return True
    
    def _read_card_thread(self):
        """Background thread to read card with timeout"""
        if not self.arduino or not self.arduino.is_open:
            self.socketio.emit('card_error', {'message': 'Arduino not connected'})
            self.reading_active = False
            return
        
        try:
            self.arduino.reset_input_buffer()
            start_time = time.time()
            
            while self.reading_active and (time.time() - start_time) < self.timeout_seconds:
                try:
                    if self.arduino.in_waiting > 0:
                        line = self.arduino.readline().decode('utf-8', errors='ignore').strip()
                        
                        # Expected format: <CARD|ABCD1234>
                        if line.startswith('<CARD|') and line.endswith('>'):
                            uid = line[6:-1]
                            if len(uid) == 8:
                                self.reading_active = False
                                
                                # Call the callback with card UID
                                if self.current_callback:
                                    self.current_callback(uid)
                                
                                # Emit success event
                                self.socketio.emit('card_read', {
                                    'success': True,
                                    'uid': uid
                                })
                                return
                    
                    time.sleep(0.1)
                
                except Exception as e:
                    logger.error("event=card_read_error error=%s", e)
                    time.sleep(0.1)
            
            # Timeout reached
            self.reading_active = False
            self.socketio.emit('card_timeout', {
                'message': f'No card detected within {self.timeout_seconds} seconds'
            })
        
        except Exception as e:
            logger.error("event=card_read_thread_error error=%s", e)
            self.socketio.emit('card_error', {'message': str(e)})
            self.reading_active = False
    
    def cancel_reading(self):
        """Cancel active card reading"""
        self.reading_active = False
        self.current_callback = None
