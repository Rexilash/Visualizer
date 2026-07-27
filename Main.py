import tkinter as tk
from VideoWriter import VideoWriter

def main():
    root = tk.Tk()
    app = VideoWriter(root)
    root.mainloop()

if __name__ == "__main__":
    main()