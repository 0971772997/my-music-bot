from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Web Server của Bot đang hoạt động 24/7!"

def run():
    # Tự động lấy Port của Render, nếu test ở máy tính thì dùng 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()