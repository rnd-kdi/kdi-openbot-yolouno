# =========================================================
# ============== by KDI EDU ===============================
# ========== https://kdi.edu.vn/ ==========================
# =========================================================

import sys
import time
try:
    import ubluetooth
except ImportError:
    print("Cảnh báo: Không tìm thấy thư viện ubluetooth. Chế độ Bluetooth sẽ không hoạt động.")
    ubluetooth = None

# This class implements a simple and efficient moving average filter.
class _MovingAverageFilter:
    """Một bộ lọc trung bình trượt đơn giản và hiệu quả."""
    def __init__(self, size=5):
        self.size = size
        self.buffer = []
        self.sum = 0

    def add(self, value):
        """Thêm một giá trị mới vào bộ lọc và trả về giá trị trung bình đã được làm mượt."""
        if len(self.buffer) == self.size:
            self.sum -= self.buffer.pop(0)
        
        self.buffer.append(value)
        self.sum += value
        
        return int(self.sum / len(self.buffer))

# This class serves as the main parser for OpenBot, handling both USB and Bluetooth connections.
# It includes methods for reading data, processing messages, and applying a moving average filter.
class OpenBotParser:
    """
    Class chính để tương tác với OpenBot.
    Hỗ trợ cả kết nối USB (0) và Bluetooth (1).
    """
    def __init__(self, connection_type=1, filter_size=5):
        """
        Khởi tạo Parser.
        :param connection_type: Loại kết nối. 0=USB, 1=Bluetooth (mặc định).
        :param filter_size: Kích thước cửa sổ cho bộ lọc trung bình trượt.
        """
        self.target_x = 0
        self.target_y = 0
        self.target_w = 0
        self.target_h = 0
        self.has_target = False
        
        if filter_size > 0:
            print(f"Parser: Kích hoạt bộ lọc trung bình trượt với kích thước = {filter_size}")
            self._filter_x = _MovingAverageFilter(filter_size)
            self._filter_y = _MovingAverageFilter(filter_size)
            self._filter_w = _MovingAverageFilter(filter_size)
            self._filter_h = _MovingAverageFilter(filter_size)
        else:
            self._filter_x = None 

        self.msg_part = 0
        self.header = ''
        self.msg_buf = ''
        
        self.p1_send_request = False
        self._tx_handle = None
        
        self._last_update_ms = 0
        self._consecutive_reads = 0
        self._max_consecutive = 3
        
        self.connection_type = -1
        self.set_connection_type(connection_type)
        



    def set_connection_type(self, connection_type):
        """Đặt loại kết nối: 0 cho USB, 1 cho Bluetooth."""
        if connection_type not in (0, 1):
            raise ValueError("Loại kết nối không hợp lệ. Chỉ chấp nhận 0 (USB) hoặc 1 (Bluetooth).")
        
        self.connection_type = connection_type
        
        if self.connection_type == 1:
            if ubluetooth:
                self._initialize_bluetooth()
            else:
                raise RuntimeError("Không thể khởi tạo Bluetooth. Thư viện ubluetooth không có sẵn.")
        else:
            print("Parser: Chế độ USB được chọn. Sẵn sàng đọc từ stdin.")
            
        return self.connection_type
        
    def get_connection_type(self):
        """Lấy loại kết nối hiện tại."""
        return self.connection_type

    # This method reads data from stdin (USB) and processes it.
    def read_stdin(self):
        """Đọc dữ liệu từ USB (stdin) với logic tối ưu hóa."""
        if self.connection_type != 0:
            return

        try:
            current_ms = self._get_time_ms()
            data_age = self._time_diff_ms(self._last_update_ms, current_ms)
            
            if data_age < 30 and self._consecutive_reads > 1:
                self._consecutive_reads = 0
                return
            
            if data_age > 50:
                self._consecutive_reads = 0
            
            self._consecutive_reads += 1
            
            if hasattr(sys.stdin, 'read'):
                chars_read = 0
                max_chars = 50 if self._consecutive_reads == 1 else 150
                data_found = False
                
                while chars_read < max_chars:
                    data = sys.stdin.read(1)
                    if not data:
                        if not data_found:
                            self._consecutive_reads = self._max_consecutive
                        break
                    
                    data_found = True
                    chars_read += 1
                    old_has_target = self.has_target
                    
                    self.process_char(data)
                    
                    if not old_has_target and self.has_target:
                        self._last_update_ms = current_ms
                    
                    if self.msg_part == 0 and self.header == '' and self.has_target:
                        break
            else: # Fallback
                data = input()
                for ch in data:
                    self.process_char(ch)
                self.process_char('\n')
                self._last_update_ms = current_ms
        except (EOFError, KeyboardInterrupt):
            pass
        except Exception as e:
            pass
        
        
    # This method initializes the Bluetooth stack and sets up the necessary services and characteristics.
    def _initialize_bluetooth(self):
        """Hàm nội bộ để khởi tạo tất cả các thành phần Bluetooth."""
        print("Parser: Đang khởi tạo ngăn xếp Bluetooth...")
        
        self._ble = ubluetooth.BLE()
        self._ble.active(False)
        time.sleep_ms(200)
        self._ble.active(True)
        print("Parser: Ngăn xếp BLE đã được kích hoạt.")

        self._ble.irq(self._irq)
        print("Parser: Đã gán hàm xử lý ngắt (IRQ).")

        _DEVICE_NAME = 'OpenBot-ESP32'
        _UART_SERVICE_UUID = ubluetooth.UUID("61653dc3-4021-4d1e-ba83-8b4eec61d613") # UUID Openbot App
        _RX_CHAR_UUID = ubluetooth.UUID("06386c14-86ea-4d71-811c-48f97c58f8c9")
        _TX_CHAR_UUID = ubluetooth.UUID("9bf1103b-834c-47cf-b149-c9e4bcf778a7")
        
        self._adv_payload = b'\x02\x01\x06\x11\x07' + _UART_SERVICE_UUID
        name_bytes = _DEVICE_NAME.encode('utf-8')
        self._scan_rsp_payload = bytes([len(name_bytes) + 1, 0x09]) + name_bytes
        
        uart_service = (_UART_SERVICE_UUID, ((_TX_CHAR_UUID, ubluetooth.FLAG_NOTIFY), (_RX_CHAR_UUID, ubluetooth.FLAG_WRITE),))
        services_handles = self._ble.gatts_register_services((uart_service,))
        self._tx_handle = services_handles[0][0] 
        self._rx_handle = services_handles[0][1]
        print(f"Parser: Dịch vụ UART đã được đăng ký, TX handle: {self._tx_handle}, RX handle: {self._rx_handle}")

        
        self._connections = set()
        self._advertise()

    def _irq(self, event, data):
        """Hàm xử lý ngắt từ BLE stack."""
        if self.connection_type != 1: return

        if event == 1:
            conn_handle, _, _ = data
            print("BLE: Đã kết nối.")
            self._connections.add(conn_handle)
            self._ble.gap_advertise(None)
        elif event == 2:
            conn_handle, _, _ = data
            print("BLE: Đã ngắt kết nối.")
            self._connections.remove(conn_handle)
            self._advertise()
        elif event == 3:
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                received_data = self._ble.gatts_read(self._rx_handle)
                for char_code in received_data:
                    self.process_char(chr(char_code))

    def _advertise(self):
        """Bắt đầu quảng bá thiết bị."""
        print("BLE: Bắt đầu quảng bá...")
        try:
            self._ble.gap_advertise(100000, adv_data=self._adv_payload, resp_data=self._scan_rsp_payload)
        except Exception as e:
            print(f"LỖI: Không thể quảng bá BLE. Lý do: {e}")

    # This method parses the received message and updates the target coordinates and dimensions.
    # It also applies the moving average filter if it is enabled.
    def parse_msg(self):
        if self.header == 't':
            try:
                parts = self.msg_buf.split(',')
                if len(parts) == 4:
                    raw_x = int(parts[0])
                    raw_y = int(parts[1])
                    raw_w = int(parts[2])
                    raw_h = int(parts[3])
                    
                    if self._filter_x:
                        self.target_x = self._filter_x.add(raw_x)
                        self.target_y = self._filter_y.add(raw_y)
                        self.target_w = self._filter_w.add(raw_w)
                        self.target_h = self._filter_h.add(raw_h)
                    else:
                        self.target_x = raw_x
                        self.target_y = raw_y
                        self.target_w = raw_w
                        self.target_h = raw_h

                    self.has_target = True
                    self._last_update_ms = self._get_time_ms()
                else:
                    self.has_target = False
            except (ValueError, IndexError):
                self.has_target = False
        
        self.msg_part = 0
        self.header = ''
        self.msg_buf = ''

    def process_char(self, char):
        if char in ('\n', '\r'):
            if self.header:
                self.parse_msg()
            return

        if self.msg_part == 0:
            self.header = char
            self.msg_part = 1
            self.msg_buf = ''
        else:
            self.msg_buf += char
            
    # This method sends a message p0 or p1.
    def send_msg(self, msg="p0"):
        """Gửi một tin nhắn qua Bluetooth đến tất cả các thiết bị đã kết nối."""
        if self.connection_type == 1:  # Bluetooth
            data_to_send = str(msg).encode('utf-8')
            # sent_count = 0
            for conn_handle in self._connections:
                try:
                    self._ble.gatts_notify(conn_handle, self._tx_handle, data_to_send)
                    # sent_count += 1
                except Exception as e:
                    print(f"LỖI: Không thể gửi tin nhắn đến handle {conn_handle}. Lý do: {e}")
                    
            # if sent_count > 0:
            #     print(f"BLE: Đã gửi '{msg}' đến {sent_count} thiết bị")

        elif self.connection_type == 0:  # USB mode
            try:
                message_to_send = f"{msg}\n"
                sys.stdout.write(message_to_send)
                sys.stdout.flush()  # Đảm bảo data được gửi ngay lập tức
                print(f"USB: Đã gửi tin nhắn '{msg}'")  # Log để debug
            except Exception as e:
                print(f"LỖI: Không thể gửi tin nhắn qua USB. Lý do: {e}")
                
        else:  # Unknown connection type
            print(f"LỖI: Loại kết nối không xác định: {self.connection_type}")

        
    def _get_time_ms(self):
        return time.ticks_ms()
        
    def _time_diff_ms(self, start, end):
        return time.ticks_diff(end, start)

    # This method retrieves the target coordinates and dimensions.
    def get_target_x(self):
        if self.connection_type == 0:
            self.read_stdin()
        return self.target_x if self.has_target else None
    
    def get_target_y(self):
        if self.connection_type == 0 and self._consecutive_reads < 2:
            self.read_stdin()
        return self.target_y if self.has_target else None
    
    def get_target_w(self):
        return self.target_w if self.has_target else None
    
    def get_target_h(self):
        return self.target_h if self.has_target else None
    
    # This function helps to debug easily by returning all target data in a tuple.
    def get_target_box(self):
        if self.connection_type == 0:
            self.read_stdin()
        if self.has_target:
            return (self.target_x, self.target_y, self.target_w, self.target_h)
        return None
    
    def is_target_available(self):
        return self.has_target
    
    def get_data_age_ms(self):
        if self.has_target:
            return self._time_diff_ms(self._last_update_ms, self._get_time_ms())
        return -1




# from yolouno_phone import OpenBotParser
# from abutton import *

# parser = OpenBotParser(0)

# btn_BOOT= aButton(BOOT_PIN)

# def deinit():
#   btn_BOOT.deinit()

# import yolo_uno
# yolo_uno.deinit = deinit

# async def task_forever():
#   while True:
#     await asleep_ms(50)
#     print((''.join([str(x) for x in ['x1: ', parser.get_target_x(), ' y2: ', parser.get_target_y(), ' w: ', parser.get_target_w(), ' h: ', parser.get_target_h()]])))
#     if btn_BOOT():
#       parser.send_msg("p1")

# async def setup():

#   print('App started')
#   await asleep_ms(5000)

#   create_task(task_forever())

# async def main():
#   await setup()
#   while True:
#     await asleep_ms(100)

# run_loop(main())




