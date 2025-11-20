from flask import Flask
from threading import Thread

app = Flask('') 

@app.route('/')
def home():
    return "I'm alive!"

import os
# ... other imports

def run():
    # Use the port environment variable Replit provides
    # This often forces Replit to treat the project as a persistent web app
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port) 


def keep_alive():
    # Start the website in the background so your bot can keep running
    t = Thread(target=run)
    t.start()
