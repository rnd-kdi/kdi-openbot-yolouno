

# ESP32 MicroPython - OpenBot Parser (Smooth Version)
import sys
import time

print("Yolouno OpenBot Parser (Smooth Reading)")
print("Sẵn sàng nhận lệnh từ điện thoại...")
print("-" * 60)

class OpenBotParser:
    def __init__(self, connection_type):
        # Data storage
        self.target_x = 0
        self.target_y = 0
        self.target_w = 0
        self.target_h = 0
        self.img_width = 0
        self.img_height = 0
        self.has_target = False
        
        # Connection type: 0=USB, 1=Bluetooth
        if connection_type not in (0, 1):
            raise ValueError("PHẢI chọn loại kết nối: USB hoặc Bluetooth")
        self.connection_type = connection_type
        # Parser state
        self.msg_part = 0  # 0=HEADER, 1=BODY
        self.header = ''
        self.msg_buf = ''
        
        # Smooth reading optimization
        self._last_update_ms = 0
        self._data_age_threshold = 100  # Consider data stale after 100ms
        self._consecutive_reads = 0
        self._max_consecutive = 3  # Max reads in a row

        
    def _get_time_ms(self):
        """Get current time in ms, compatible with different MicroPython versions"""
        try:
            return time.ticks_ms()
        except:
            return int(time.time() * 1000)
            
    def _time_diff_ms(self, start, end):
        """Calculate time difference, compatible with different versions"""
        try:
            return time.ticks_diff(end, start)
        except:
            return end - start
        
    def set_connection_type(self, connection_type):
        """Set connection type: 0=USB, 1=Bluetooth"""
        if connection_type not in (0, 1):
            raise ValueError("PHẢI chọn loại kết nối: USB hoặc Bluetooth")
        self.connection_type = connection_type
        return self.connection_type
        
    def get_connection_type(self):
        """Get current connection type"""
        return self.connection_type
        
    def read_stdin(self):
        """Adaptive read - reads more when data is available, less when not"""
        try:
            if self.connection_type == 0:  # USB connection
                # Check if we should skip reading
                current_ms = self._get_time_ms()
                data_age = self._time_diff_ms(self._last_update_ms, current_ms)
                
                # If data is fresh and we've read recently, skip
                if data_age < 30 and self._consecutive_reads > 1:
                    self._consecutive_reads = 0
                    return
                    
                # Reset consecutive counter if enough time passed
                if data_age > 50:
                    self._consecutive_reads = 0
                
                # Track consecutive reads
                self._consecutive_reads += 1
                
                # Adaptive read amount based on data availability
                if hasattr(sys.stdin, 'read'):
                    chars_read = 0
                    max_chars = 50 if self._consecutive_reads == 1 else 150
                    data_found = False
                    
                    while chars_read < max_chars:
                        data = sys.stdin.read(1)
                        if not data:
                            # No data available
                            if not data_found:
                                # No data at all, reduce future reads
                                self._consecutive_reads = self._max_consecutive
                            break
                        
                        data_found = True
                        chars_read += 1
                        old_has_target = self.has_target
                        
                        self.process_char(data)
                        
                        # If we just got new target data, update timestamp
                        if not old_has_target and self.has_target:
                            self._last_update_ms = current_ms
                        
                        # Stop after parsing one complete message
                        if self.msg_part == 0 and self.header == '' and self.has_target:
                            break
                            
                else:
                    # Fallback for input()
                    try:
                        # if set_connection_type() == 0:  # USB
                        data = input()
                        for ch in data:
                            self.process_char(ch)
                        self.process_char('\n')
                        self._last_update_ms = current_ms
                        # else:  # Bluetooth
                        
                    
                        
                    except EOFError:
                        pass
            elif self.connection_type == 1:  # Bluetooth connection
                # Read from Bluetooth connection
                print("Reading from Bluetooth...")
                
            else:
                raise ValueError("Invalid connection type. Use 0 for USB or 1 for Bluetooth.")    
                    
                    
        except Exception as e:
            # Silent fail
            pass

    def parse_msg(self):
        """Parse message"""
        h = self.header
        buf = self.msg_buf

        if h == 't':  # Target data
            try:
                parts = buf.split(',')
                if len(parts) == 6:
                    # Parse all values
                    new_x = int(parts[0])
                    new_y = int(parts[1])
                    new_w = int(parts[2])
                    new_h = int(parts[3])
                    new_img_w = int(parts[4])
                    new_img_h = int(parts[5])
                    
                    # Update all at once
                    self.target_x = new_x
                    self.target_y = new_y
                    self.target_w = new_w
                    self.target_h = new_h
                    self.img_width = new_img_w
                    self.img_height = new_img_h
                    self.has_target = True
                    
                else:
                    self.has_target = False
            except:
                self.has_target = False

        # Reset state
        self.msg_part = 0
        self.header = ''
        self.msg_buf = ''

    def process_char(self, char):
        """Process single character"""
        if char in ('\n', '\r'):
            if self.header:
                self.parse_msg()
            else:
                # Reset if empty line
                self.msg_part = 0
                self.header = ''
                self.msg_buf = ''
            return

        if self.msg_part == 0:  # HEADER
            self.header = char
            self.msg_part = 1
            self.msg_buf = ''
        else:  # BODY
            self.msg_buf += char

    # Public API
    def get_target_x(self):
        self.read_stdin()
        return self.target_x if self.has_target else None
    
    def get_target_y(self):
        # Don't read again if just read in get_target_x
        if self._consecutive_reads < 2:
            self.read_stdin()
        return self.target_y if self.has_target else None
    
    def get_target_w(self):
        # Don't read again
        return self.target_w if self.has_target else None
    
    def get_target_h(self):
        # Don't read again
        return self.target_h if self.has_target else None
    
    def get_target_box(self):
        self.read_stdin()
        if self.has_target:
            return (self.target_x, self.target_y, self.target_w, self.target_h)
        return None
    
    def get_image_size(self):
        if self.has_target:
            return (self.img_width, self.img_height)
        return None
    
    def is_target_available(self):
        return self.has_target
    
    def get_data_age_ms(self):
        """Get age of current data in milliseconds"""
        if self.has_target:
            current = self._get_time_ms()
            return self._time_diff_ms(self._last_update_ms, current)
        return -1




# from yolouno_phone import OpenBotParser

# parser = OpenBotParser()

# async def task_forever():
#   while True:
#     await asleep_ms(50)
#     print((''.join([str(x) for x in ['x: ', parser.get_target_x(), ' y: ', parser.get_target_y(), ' w: ', parser.get_target_w(), ' h: ', parser.get_target_h()]])))

# async def setup():

#   print('App started')

#   create_task(task_forever())

# async def main():
#   await setup()
#   while True:
#     await asleep_ms(100)

# run_loop(main())
