from app import create_app
import threading
import requests
import time
import os



def keep_alive():
    while True:
        try:
            requests.get("https://github-comparison.onrender.com/")
            print("Pinged the app to keep it alive!")
        except Exception as e:
            print(f"Error pinging: {e}")
        time.sleep(15) 

# Start keep_alive() in a separate thread
threading.Thread(target=keep_alive, daemon=True).start()

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Default to 10000 if PORT isn't set
    app.run(host="0.0.0.0", port=port)
