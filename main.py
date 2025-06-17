import subprocess
import sys
import os

def run_streamlit_app():
    """Runs the Streamlit application."""
    app_path = os.path.join(os.path.dirname(__file__), "src", "streamlit_app", "app.py")
    print(f"Attempting to run Streamlit app from: {app_path}")
    try:
        # Use subprocess.run to execute the streamlit command
        # This assumes 'streamlit' is in the system's PATH or activated virtual environment
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], check=True)
    except FileNotFoundError:
        print("Error: 'streamlit' command not found. Please ensure Streamlit is installed and in your PATH.")
        print("You can install it using: pip install streamlit")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")
        print(f"Streamlit output: {e.stdout.decode() if e.stdout else 'N/A'}")
        print(f"Streamlit error: {e.stderr.decode() if e.stderr else 'N/A'}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("Starting AlertRx application...")
    run_streamlit_app()
