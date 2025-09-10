import os
import logging
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Validate required environment variables
def validate_environment_variables():
    required_vars = ["SESSION_SECRET", "DATABASE_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.error("Please configure the following environment variables in your deployment:")
        for var in missing_vars:
            logging.error(f"  - {var}")
        sys.exit(1)

# Validate environment on startup
validate_environment_variables()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

# Import routes to register endpoints
import routes  # noqa: F401

with app.app_context():
    # Import models 
    import models  # noqa: F401
    
    # Create all tables with error handling
    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        logging.error("Please check your DATABASE_URL configuration and database connectivity")
        logging.error("Application will exit - database connection is required for proper functionality")
        sys.exit(1)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
