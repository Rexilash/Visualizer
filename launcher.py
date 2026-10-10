import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    frontend_exe = os.path.join(base_dir, "frontend", "visualizer.exe")

    # Launch Flutter UI directly
    frontend_proc = subprocess.Popen([frontend_exe])
    frontend_proc.wait()

if __name__ == "__main__":
    main()