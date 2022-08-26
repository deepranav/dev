app_url = "https://exmaple-test-ong.onrender.com"

import time
import requests
import threading

def keep_alive():
    print("Keep Alive")
    while True:
        try:
            requests.get(app_url)
        except:
            print("Keep Alive Error")
        else:
            time.sleep(60 * 5)
threading.Thread(target=keep_alive).start()


print(111)
from main import main
print("222")
threading.Thread(target=main).start()
print("333")


from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'
