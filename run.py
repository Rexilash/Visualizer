import os
import sys
import subprocess

def main():
    print("Starting Visualizer Development Environment...")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Locate frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if not os.path.exists(frontend_dir):
        print("Error: 'frontend' directory not found!", file=sys.stderr)
        sys.exit(1)
        
    print("Launching Flutter frontend via 'flutter run'...")
    
    # Enable shell execution on Windows so batch scripts like 'flutter' are found
    use_shell = os.name == 'nt'
    flutter_cmd = ["flutter", "run"]
    
    try:
        flutter_process = subprocess.Popen(flutter_cmd, cwd=frontend_dir, shell=use_shell)
        flutter_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down development environment...")
        flutter_process.terminate()
        flutter_process.wait()
    except Exception as e:
        print(f"Error launching Flutter: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()