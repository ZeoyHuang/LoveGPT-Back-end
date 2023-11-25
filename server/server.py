import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from routes import chat_bp
from models import db
from flasgger import Swagger, swag_from
from config.swagger import template, swagger_config

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = url

db.init_app(app)
SWAGGER = {"title": "LoveGPT API", "uiversion": 3}

app.register_blueprint(chat_bp)

Swagger(app, config=swagger_config, template=template)


@app.route("/")
@swag_from("./docs/index.yaml")
def index():
    return "Hello World"
    # return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="88", debug=True)
