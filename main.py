from app import create_app
import threading
import requests
import time

flask_app = create_app()

def keep_alive():
    while True:
        try:
            requests.get("hhttps://github-comparison.onrender.com/")
            print("Pinged the app to keep it alive!")
        except Exception as e:
            print(f"Error pinging: {e}")
        time.sleep(600)  # Ping every 10 minutes

# Start keep_alive() in a separate thread
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    flask_app.run()
