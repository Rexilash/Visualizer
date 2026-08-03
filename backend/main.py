import tkinter as tk
from backend.gui import VisualizerApp

def main():
    root = tk.Tk()
    app = VisualizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()