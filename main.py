import pigpio
import time
from datetime import datetime

GPIO_PIN = 17  # Change this to the GPIO pin you're using

pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("Could not connect to pigpio daemon. Is 'pigpiod' running?")

pi.set_mode(GPIO_PIN, pigpio.OUTPUT)

def bcd_encode(value, bits):
    bcd = []
    digits = list(f"{value:0{(bits + 3) // 4}d}")
    for digit in reversed(digits):
        bcd_digit = f"{int(digit):04b}"
        bcd.extend(reversed([bool(int(b)) for b in bcd_digit]))
    return list(reversed(bcd))[-bits:]

def generate_irig_b_frame():
    frame = [False] * 60

    now = datetime.utcnow()
    seconds = now.second
    minutes = now.minute
    hours = now.hour
    day_of_year = now.timetuple().tm_yday

    # Mark position identifiers
    for pos in range(0, 60, 10):
        frame[pos] = True  # We'll use this to send 800ms pulse

    # Seconds: bits 1–8
    frame[1:9] = bcd_encode(seconds, 8)

    # Minutes: bits 10–17
    frame[10:18] = bcd_encode(minutes, 8)

    # Hours: bits 20–27
    frame[20:28] = bcd_encode(hours, 8)

    # Day of year: bits 30–39, 40–48
    day_bcd = bcd_encode(day_of_year, 17)
    frame[30:40] = day_bcd[:10]
    frame[40:49] = day_bcd[10:]

    return frame

def send_irig_b_frame(frame):
    for i, bit in enumerate(frame):
        print(f"Bit {i:02d}: ", end='')

        if i % 10 == 0:
            # Position Identifier: 800ms pulse
            print("P (position marker)")
            pi.write(GPIO_PIN, 1)
            time.sleep(0.8)
            pi.write(GPIO_PIN, 0)
            time.sleep(0.2)
        elif bit:
            # Binary 1: 500ms high
            print("1")
            pi.write(GPIO_PIN, 1)
            time.sleep(0.5)
            pi.write(GPIO_PIN, 0)
            time.sleep(0.5)
        else:
            # Binary 0: 200ms high
            print("0")
            pi.write(GPIO_PIN, 1)
            time.sleep(0.2)
            pi.write(GPIO_PIN, 0)
            time.sleep(0.8)

try:
    while True:
        frame = generate_irig_b_frame()
        send_irig_b_frame(frame)
        print("IRIG-B frame sent.\n")

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    pi.write(GPIO_PIN, 0)
    pi.stop()
