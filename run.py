from game_app import create_app

app = create_app()

if __name__ == '__main__':
    # You can run this file directly using "python run.py"
    # The server will be available at http://127.0.0.1:8888
    app.run(debug=True, port=8888)