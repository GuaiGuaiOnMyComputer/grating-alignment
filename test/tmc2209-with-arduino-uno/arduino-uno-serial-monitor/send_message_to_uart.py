import serial
import time

# Configure the UART serial port
ser = serial.Serial(
    port="/dev/ttyACM0",    # UART1 on Jetson Orin Nano
    baudrate=115200,          # Match Arduino's baudrate
    timeout=1
)

count = 1

try:
    while True:
        message = f"helloworld{count}\n"   # '\n' optional, often used as end-of-line
        ser.write(message.encode('ascii'))
        print(f"📤 Sent: {message.strip()}")
        count += 1

        while ser.in_waiting > 0:
            print(ser.read().decode('ascii'), end='', flush=True)

        time.sleep(1)  # send every 1 second

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    ser.close()
