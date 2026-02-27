from flask import Flask, render_template
from flask_cors import CORS
from app.database.database import db

# Import des blueprints
from app.routes.users_routes import user_bp
from app.routes.categories_routes import category_bp
from app.routes.listings_routes import listing_bp
from app.routes.photos_routes import photo_bp
from app.routes.buyer_protection_config_routes import config_bp
from app.routes.browse_listings_routes import browse_bp
from app.routes.addresses_routes import address_bp
from app.routes.purchases_routes import purchase_bp
from app.routes.credits_routes import credit_bp


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# AJOUT CRUCIAL : Définit l'adresse absolue pour les URL de photos (Tier A)
app.config['BASE_URL'] = 'http://127.0.0.1:5000' 

db.init_app(app)
CORS(app)

# Enregistrement des blueprints
app.register_blueprint(user_bp)
app.register_blueprint(category_bp)
app.register_blueprint(listing_bp)
app.register_blueprint(photo_bp)
app.register_blueprint(config_bp)
app.register_blueprint(browse_bp)
app.register_blueprint(address_bp)
app.register_blueprint(purchase_bp)
app.register_blueprint(credit_bp)
@app.route('/')
def index():
    """
    Route racine : Charge la page d'accueil (index.html).
    Accessible via http://localhost:5000/
    """
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_html(filename):
    """
    Route magique : Sert n'importe quelle autre page HTML demandée.
    Exemple : http://localhost:5000/login.html -> Affiche templates/login.html
    """
    # Petite sécurité pour éviter de remonter dans les dossiers (../)
    if '..' in filename or not filename.endswith('.html'):
        return "Not Found", 404
    return render_template(filename)

# Création des tables si elles n'existent pas
with app.app_context():
    
    db.create_all()
