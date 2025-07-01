import pigpio
import time
from datetime import datetime

GPIO_PIN = 17  # Change this to the GPIO pin you're using

pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("Could not connect to pigpio daemon. Is 'pigpiod' running?")

pi.set_mode(GPIO_PIN, pigpio.OUTPUT)

from datetime import datetime

def bcd_encode(value, bits):
    """Encode a decimal value into a fixed-length BCD boolean array."""
    num_digits = (bits + 3) // 4
    bcd = []

    for digit in reversed(f"{value:0{num_digits}d}"):
        bits4 = [bool(int(b)) for b in f"{int(digit):04b}"]
        bcd = bits4 + bcd

    return bcd[-bits:]

def generate_irig_b_frame():
    frame = [False] * 60

    now = datetime.utcnow()
    seconds = now.second
    minutes = now.minute
    hours = now.hour
    day_of_year = now.timetuple().tm_yday

    print(f"\nEncoding time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')} | Day of Year: {day_of_year}")

    # Position identifiers: every 10th bit
    for pos in range(0, 60, 10):
        frame[pos] = True

    # Set each field in BCD
    frame[1:9] = bcd_encode(seconds, 8)
    frame[10:18] = bcd_encode(minutes, 8)
    frame[20:28] = bcd_encode(hours, 8)

    day_bcd = bcd_encode(day_of_year, 17)
    frame[30:40] = day_bcd[:10]
    frame[40:49] = day_bcd[10:]

    # Debug: Print full IRIG-B frame
    frame_str = ''.join(['1' if b else '0' for b in frame])
    print(f"IRIG-B Frame: {frame_str}")

    assert len(frame) == 60, f"Frame is {len(frame)} bits instead of 60"
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
