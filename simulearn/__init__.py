from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config

# Initialize the SQLAlchemy database object
db = SQLAlchemy()

# Create a Flask application instance
app = Flask(__name__)

# Load configuration settings from the Config class
app.config.from_object(Config)

# Initialize the database with the Flask application instance
db.init_app(app)

# Initialize the Flask-Mail extension with the Flask application
mail = Mail(app)

# Import routes and models from the simulearn package
from simulearn import routes, models

# Create all database tables
with app.app_context():
    db.create_all()