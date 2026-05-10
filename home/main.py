from home import app
from flask import render_template, request, send_file

@app.route('/')
def index():
    return render_template('index.html')
