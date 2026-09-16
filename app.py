from flask import Flask
from configs import config_all

def create_app():
    app = Flask(__name__)

    config_all(app)   

    return app

if __name__ == '__main__':
    app = create_app()

    app.run(debug=True)