from flask import Flask
from threading import Thread

app = Flask('')
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
@app.route('/123987')
def data():
    with open('Recources/prefixes.json', 'r') as file:
        data = file.read()
    return data

@app.route('/')
def home():
    return "all up"

def run():
  try:
    app.run(host='0.0.0.0',port=8080)
  except:
    pass

def keep_alive():  
    t = Thread(target=run)
    t.start()