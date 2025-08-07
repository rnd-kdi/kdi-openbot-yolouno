OpenBot Parser for ESP32
A versatile MicroPython library to connect your ESP32 board to the OpenBot app, supporting both USB and Bluetooth LE. It includes a built-in filter to smooth out control data for more stable robot movement.

✨ Features
Dual Connection: Easily switch between USB (for debugging) and Bluetooth LE (for wireless operation).

Data Smoothing: Integrated Moving Average Filter to eliminate signal noise for smoother robot control.

High Performance: Uses interrupts for Bluetooth to ensure low-latency, CPU-efficient communication.

Simple API: Easy to use. Just initialize the class and call get_ methods to retrieve data.

Configurable: Customize the filter size to balance between smoothness and responsiveness.

🔧 Requirements
An ESP32-based board.
MicroPython firmware installed.
Openbot App on android.

🚀 Quick Start
Upload the yolouno_ble.py file to your ESP32's root directory.

Use the following code in your main.py file to get started:

# --- CONFIGURATION ---
# connection_type: 1 for Bluetooth, 0 for USB
# filter_size: 5 is a good starting point

✍️ Author
KDI EDU