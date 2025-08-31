# lifegame.py
# Conway's Game of Life for PicoCalc

import micropython
import time
import random
from picocalc import display, terminal, keyboard

# --- Constants ---
# Screen dimensions
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 312

# Cell size in pixels
CELL_SIZE = 4 

# Grid dimensions based on screen and cell size
GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE

# Colors (using pico8 palette)
COLOR_DEAD = 0  # Black
COLOR_ALIVE = 7 # White
COLOR_BORN = 11 # Green/Cyan
COLOR_DIED = 8  # Red

class LifeGame:
    """
    Manages the Game of Life simulation.
    """
    def __init__(self, width=GRID_WIDTH, height=GRID_HEIGHT):
        self.width = width
        self.height = height
        # Use two buffers for the grid to calculate the next state
        self.grid = self._create_grid()
        self.next_grid = self._create_grid()
        self.randomize_grid()
        self.paused = False
        self.running = True
        self.generation = 0

    def _create_grid(self):
        """Creates a 1D bytearray for the grid for memory efficiency."""
        return bytearray(self.width * self.height)

    def randomize_grid(self):
        """Fills the grid with a random pattern."""
        for i in range(len(self.grid)):
            self.grid[i] = random.randint(0, 1)

    @micropython.native
    def step(self):
        """Calculates the next generation of the grid."""
        self.generation += 1
        for y in range(self.height):
            for x in range(self.width):
                # Count live neighbors
                live_neighbors = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        
                        # Wrap around the edges (toroidal array)
                        nx, ny = (x + dx) % self.width, (y + dy) % self.height
                        if self.grid[ny * self.width + nx]:
                            live_neighbors += 1
                
                # Apply Game of Life rules
                current_index = y * self.width + x
                is_alive = self.grid[current_index]
                
                if is_alive:
                    if live_neighbors < 2 or live_neighbors > 3:
                        self.next_grid[current_index] = 0 # Dies
                    else:
                        self.next_grid[current_index] = 1 # Survives
                else:
                    if live_neighbors == 3:
                        self.next_grid[current_index] = 1 # Becomes alive
                    else:
                        self.next_grid[current_index] = 0 # Stays dead

        # Swap grids for the next iteration
        self.grid, self.next_grid = self.next_grid, self.grid

    def _draw_changed_cells(self, use_highlight_colors):
        """
        A helper method to draw only the cells that have changed since the last step.
        It can draw with highlight colors or normal colors based on the parameter.
        """
        for y in range(self.height):
            for x in range(self.width):
                index = y * self.width + x
                
                old_state = self.next_grid[index]
                new_state = self.grid[index]

                if old_state == new_state:
                    continue

                # Determine the color based on the mode (highlight vs normal)
                if use_highlight_colors:
                    color = COLOR_BORN if new_state == 1 else COLOR_DIED
                else:
                    color = COLOR_ALIVE if new_state == 1 else COLOR_DEAD
                
                start_x, start_y = x * CELL_SIZE, y * CELL_SIZE
                for i in range(CELL_SIZE):
                    for j in range(CELL_SIZE):
                        display.pixel(start_x + j, start_y + i, color)

    def draw_highlights(self):
        """Draws highlights for cells that just changed state."""
        self._draw_changed_cells(use_highlight_colors=True)

    def reset_highlights(self):
        """Draws the current state over the highlighted cells with normal colors."""
        self._draw_changed_cells(use_highlight_colors=False)

    def draw_full_grid(self):
        """Draws the entire grid, used for initialization."""
        for y in range(self.height):
            for x in range(self.width):
                index = y * self.width + x
                color = COLOR_ALIVE if self.grid[index] else COLOR_DEAD
                start_x, start_y = x * CELL_SIZE, y * CELL_SIZE
                for i in range(CELL_SIZE):
                    for j in range(CELL_SIZE):
                        display.pixel(start_x + j, start_y + i, color)

    def run(self):
        """Main loop to run the simulation."""
        # --- Initialization ---
        display.switchPredefinedLUT('pico8')
        terminal.wr("\x1b[?25l") # Hide cursor
        
        self.draw_full_grid()

        try:
            temp_key_buffer = bytearray(1)
            while self.running:
                # Helper function to display status
                def update_status(process_name):
                    # \x1b[40;1H -> Move to line 40, col 1. \x1b[K -> Clear line.
                    status_text = f"Gen: {self.generation}, {process_name}"
                    terminal.wr(f"\x1b[40;1H\x1b[K{status_text}")

                # Check for user input
                if keyboard.readinto(temp_key_buffer):
                    key_char = chr(temp_key_buffer[0])
                    if key_char in ('p', 'P'):
                        self.paused = not self.paused
                        if not self.paused:
                            # Redraw the whole screen on resume
                            self.draw_full_grid()
                    elif key_char in ('q', 'Q'):
                        self.running = False

                # --- Update and Draw ---
                if not self.paused:
                    # Wait 3 seconds on the black and white view
                    update_status(f"Displaying Gen {self.generation}")
                    time.sleep(3.0)

                    # Check for input again during the long wait
                    if keyboard.readinto(temp_key_buffer): continue

                    # Calculate and draw highlights
                    update_status("Calculating next generation")
                    self.step()
                    
                    update_status("Drawing highlights")
                    self.draw_highlights()

                    # Wait 1 second on the highlighted view
                    update_status("Displaying highlights")
                    time.sleep(1.0)

                    # Finalize the generation by resetting highlights to normal colors
                    update_status("Finalizing generation display")
                    self.reset_highlights()
                
                # --- Display Status ---
                if self.paused:
                    paused_text = f"PAUSED (Gen: {self.generation}) | P:Resume Q:Quit"
                    terminal.wr(f"\x1b[40;1H\x1b[K{paused_text}")
                    time.sleep(0.1) # Add a small delay in paused state to reduce CPU usage
                else:
                    # This status is shown before the 3-second wait of the next cycle
                    update_status(f"End of Gen {self.generation}")

        finally:
            # --- Cleanup ---
            display.fill(0)
            display.restLUT()
            terminal.wr("\x1b[2J\x1b[H")
            terminal.wr("\x1b[?25h") # Show cursor
            print("Life Game finished.")


# --- Main Execution ---
if __name__ == "__main__":
    game = LifeGame(GRID_WIDTH, GRID_HEIGHT)
    game.run()
