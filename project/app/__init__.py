from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Charge le .env
    load_dotenv()
    
    # Initialise Flask
    app = Flask(__name__)
    
    # Enregistre les routes
    from app.routes import main_routes
    app.register_blueprint(main_routes)
    
    return app