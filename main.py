import time
import network
import socket
import urequests
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY
from secrets import SSID, PASSWORD  # Import Wi-Fi credentials

# Constants
BACKGROUND_COLOUR = (10, 0, 96)  # Blue background
WHITE = (255, 255, 255)  # White for unchanged price or symbol
DIM_WHITE = (204, 204, 204)  # BTC symbol dimmed by 20%
GREEN = (0, 255, 0)  # Green for price increase
RED = (255, 0, 0)  # Red for price decrease
YELLOW = (255, 255, 0)  # Yellow for connecting
BRIGHTNESS = 0.25  # Display brightness
CRYPTO_SYMBOL = "BTC"  # Cryptocurrency symbol
URL = f'https://www.bitstamp.net/api/v2/ticker/{CRYPTO_SYMBOL.lower()}usd/'

# Fixed vertical center position
CENTER_Y = 2  # Keeps text vertically aligned at y + 2 pixels from the top

# Create Galactic Unicorn object and graphics surface for drawing
gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY)
gu.set_brightness(BRIGHTNESS)

# Set font to bitmap8
graphics.set_font("bitmap8")

# Function to interpolate between two colors for a fade effect
def fade_color(color_from, color_to, step, total_steps):
    return tuple(
        int(color_from[i] + (color_to[i] - color_from[i]) * step / total_steps)
        for i in range(3)
    )

# Function for drawing outlined text
def outline_text(text, x, y, color):
    outline = (0, 0, 0)  # Black outline
    graphics.set_pen(graphics.create_pen(*outline))
    graphics.text(text, x - 1, y - 1, -1, 1)
    graphics.text(text, x, y - 1, -1, 1)
    graphics.text(text, x + 1, y - 1, -1, 1)
    graphics.text(text, x - 1, y, -1, 1)
    graphics.text(text, x + 1, y, -1, 1)
    graphics.text(text, x - 1, y + 1, -1, 1)
    graphics.text(text, x, y + 1, -1, 1)
    graphics.text(text, x + 1, y + 1, -1, 1)

    graphics.set_pen(graphics.create_pen(*color))
    graphics.text(text, x, y, -1, 1)

# Function to update the Wi-Fi LED indicator
def update_wifi_led(color, flashing=False):
    x = GalacticUnicorn.WIDTH - 1  # Rightmost pixel
    y = 0  # Top row
    graphics.set_pen(graphics.create_pen(*color))
    graphics.pixel(x, y)
    gu.update(graphics)
    if flashing:
        time.sleep(0.5)
        graphics.set_pen(graphics.create_pen(*BACKGROUND_COLOUR))
        graphics.pixel(x, y)
        gu.update(graphics)
        time.sleep(0.5)

# Function to check internet connectivity
def is_internet_connected():
    try:
        addr = socket.getaddrinfo("8.8.8.8", 80)[0][-1]  # Google's DNS
        s = socket.socket()
        s.settimeout(3)  # Timeout for the connection attempt
        s.connect(addr)
        s.close()
        return True
    except Exception as e:
        print(f"Internet check failed: {e}")
        return False

# Function to continuously monitor and reconnect Wi-Fi if needed
def maintain_wifi_connection():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        if wlan.isconnected():
            print("Wi-Fi connected. Checking internet...")
            if is_internet_connected():
                print("Internet connected.")
                update_wifi_led(GREEN, flashing=False)  # Solid green for success
                return  # Exit the function when everything is working
            else:
                print("Internet unreachable. Retrying...")
                update_wifi_led(RED, flashing=True)  # Flash red for internet issue
        else:
            print("Wi-Fi disconnected. Reconnecting...")
            wlan.connect(SSID, PASSWORD)
            for _ in range(10):  # Try for 10 seconds
                if wlan.isconnected():
                    break
                update_wifi_led(YELLOW, flashing=True)  # Flash yellow for Wi-Fi reconnection
                time.sleep(1)

        # Retry every 5 seconds if either Wi-Fi or internet fails
        time.sleep(5)

# Function to fetch the latest cryptocurrency price
def fetch_crypto_price():
    try:
        response = urequests.get(URL)
        data = response.json()
        response.close()
        return int(float(data['last']))  # Convert to integer
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None  # Return None if fetching fails

# Function to handle scrolling and fading
def scroll_and_fade(symbol, last_price, new_price, color_from, color_to, scroll_direction):
    symbol_width = graphics.measure_text(symbol, 1)

    # Perform scrolling over 10 steps
    for offset in range(0, 10):  # Smooth scrolling over 10 steps
        graphics.set_pen(graphics.create_pen(*BACKGROUND_COLOUR))
        graphics.clear()

        # Scroll `BTC:` symbol in the opposite direction of the value
        outline_text(symbol, 1, CENTER_Y - offset * scroll_direction, DIM_WHITE)
        outline_text(symbol, 1, CENTER_Y - (offset - 10) * scroll_direction, DIM_WHITE)

        # Scroll price value in the intended direction
        outline_text(
            f"${last_price}",
            1 + symbol_width,
            CENTER_Y + offset * scroll_direction,
            fade_color(color_from, color_to, offset, 10),
        )
        outline_text(
            f"${new_price}",
            1 + symbol_width,
            CENTER_Y + (offset - 10) * scroll_direction,
            fade_color(color_from, color_to, offset, 10),
        )

        gu.update(graphics)
        time.sleep(0.05)

    # After scrolling, ensure the final position is correctly aligned
    graphics.set_pen(graphics.create_pen(*BACKGROUND_COLOUR))
    graphics.clear()
    outline_text(symbol, 1, CENTER_Y, DIM_WHITE)  # Align symbol to CENTER_Y
    outline_text(f"${new_price}", 1 + symbol_width, CENTER_Y, color_to)  # Align value to CENTER_Y
    gu.update(graphics)

# Main loop
def main_loop():
    last_price = fetch_crypto_price() or 0
    current_color = WHITE  # Initial color for unchanged price

    while True:
        # Ensure Wi-Fi and internet connectivity
        print("Checking Wi-Fi and internet connectivity...")
        maintain_wifi_connection()

        # Fetch the latest price
        print("Fetching cryptocurrency price...")
        new_price = fetch_crypto_price()
        if new_price is None:
            print("Failed to fetch price. Retrying in 10 seconds...")
            time.sleep(10)
            continue

        # Determine scroll direction and color changes
        if new_price > last_price:
            print(f"Price increased: {last_price} -> {new_price}")
            scroll_direction = -1  # Scroll up
            color_from, color_to = current_color, GREEN
            current_color = GREEN
        elif new_price < last_price:
            print(f"Price decreased: {last_price} -> {new_price}")
            scroll_direction = 1  # Scroll down
            color_from, color_to = current_color, RED
            current_color = RED
        else:
            print(f"Price unchanged: {last_price}")
            scroll_direction = 0  # No scrolling
            color_from, color_to = current_color, WHITE
            current_color = WHITE

        # Handle scrolling and fading
        if scroll_direction != 0:
            scroll_and_fade(f"{CRYPTO_SYMBOL}:", last_price, new_price, color_from, color_to, scroll_direction)
        else:
            # Fade to white without scrolling
            for step in range(10):
                graphics.set_pen(graphics.create_pen(*BACKGROUND_COLOUR))
                graphics.clear()
                outline_text(f"{CRYPTO_SYMBOL}:", x=1, y=CENTER_Y, color=DIM_WHITE)
                outline_text(
                    f"${new_price}",
                    x=1 + graphics.measure_text(f"{CRYPTO_SYMBOL}:", 1),
                    y=CENTER_Y,
                    color=fade_color(color_from, color_to, step, 10),
                )
                gu.update(graphics)
                time.sleep(0.05)

        # Update last_price for the next iteration
        last_price = new_price
        time.sleep(10)

# Entry point
if __name__ == "__main__":
    print("Starting main program...")
    main_loop()

