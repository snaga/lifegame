# verify_picocalc.py
# A simple script to verify the usage of PicoCalc libraries.

from picocalc import display, terminal, keyboard
import time

def verify():
    """
    Runs a simple verification test for PicoCalc libraries.
    """
    # --- Initialization ---
    # Use a color palette (pico8 is a good choice)
    display.switchPredefinedLUT('pico8')
    
    # Hide cursor
    terminal.wr("\x1b[?25l")
    
    # --- Main Test Logic ---
    try:
        # 1. Fill the screen with a blue color (color index 2 in pico8 palette)
        blue_color = 2
        display.fill(blue_color)

        # 2. Draw a white rectangle in the center
        white_color = 7
        rect_w, rect_h = 80, 60
        start_x = (320 - rect_w) // 2
        start_y = (312 - rect_h) // 2
        
        for y in range(start_y, start_y + rect_h):
            for x in range(start_x, start_x + rect_w):
                display.pixel(x, y, white_color)

        # 3. Display a message at the bottom
        terminal.wr("\x1b[40;1HPress any key to exit...")

        # 4. Wait for any key press
        temp_key_buffer = bytearray(1)
        while not keyboard.readinto(temp_key_buffer):
            time.sleep(0.1)

    finally:
        # --- Cleanup ---
        # 5. Clear the screen and reset states
        display.fill(0)
        display.restLUT()
        terminal.wr("\x1b[2J\x1b[H") # Clear terminal buffer and move cursor to top
        terminal.wr("\x1b[?25h")  # Show cursor
        print("Verification script finished.")

# This allows the script to be run directly
if __name__ == "__main__":
    verify()
