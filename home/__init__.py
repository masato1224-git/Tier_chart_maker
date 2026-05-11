from flask import Flask, render_template, request, send_file
import os
#app = Flask(__name__, template_folder='home/templates', static_folder='home/static')
app = Flask(__name__)
app.secret_key = 'tier_chart_maker_secret_2024' 
from home import main

