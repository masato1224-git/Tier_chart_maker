from flask import Flask, render_template, request, send_file
import os
app = Flask(__name__)
app.secret_key = 'tier_chart_maker_secret_2024' 


