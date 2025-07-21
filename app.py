from flask import Flask, render_template, jsonify, request
import json
import random

app = Flask(__name__)

# Game state
grid_size = 10
teams = {}
points = []
lines = []
game_log = []
turn = 0

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # You can run this file directly using "python app.py"
    # The server will be available at http://127.0.0.1:8888
    app.run(debug=True, port=8888)