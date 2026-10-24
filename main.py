"""
CYBER NOVA: ODYSSEY
Retro Synthwave Space Combat Rogue-lite
Created entirely in Python using standard libraries (Tkinter, Math, Wave, Winsound).

To run:
    python main.py
    or
    py main.py
"""

import sys
import tkinter as tk
from game import Game


def setup_high_dpi():
    """Enable high-DPI scaling on Windows for ultra crisp graphics."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def main():
    setup_high_dpi()
    root = tk.Tk()
    root.title("CYBER NOVA: ODYSSEY")
    
    # Instantiate Game Engine
    app = Game(root)
    
    # Center window on screen
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = root.winfo_width()
    win_h = root.winfo_height()
    pos_x = max(0, (screen_w - win_w) // 2)
    pos_y = max(0, (screen_h - win_h) // 2)
    root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

    root.mainloop()


if __name__ == "__main__":
    main()
