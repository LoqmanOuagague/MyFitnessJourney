from app.app import app
from app.database.database import db

# ⚠️ ORDRE CRUCIAL DES IMPORTS ⚠️
# 1. Les Indépendants (ceux qui n'ont pas de ForeignKey)
from app.models.users import User
from app.models.categories import Category
from app.models.buyer_protection_config import BuyerProtectionConfig

# 2. Les Dépendants de niveau 1 (ceux qui pointent vers User ou Category)
from app.models.listings import Listing, ListingStatus
from app.models.addresses import Address
from app.models.credits import CreditTxn

# 3. Les Dépendants de niveau 2 (ceux qui pointent vers Listing)
from app.models.photos import Photo
from app.models.purchases import Purchase

import hashlib

def init_data():
    print("🚀 Initialisation de la base de données...")
    
    with app.app_context():
        # 1. On remet à zéro
        db.drop_all()
        db.create_all()

        # 2. CONFIGURATION (Vital pour le calcul des prix)
        print("⚙️  Config Buyer Protection...")
        config = BuyerProtectionConfig(id=1, ratio_percent=5.5, bias_cents=200)
        db.session.add(config)

        # 3. UTILISATEURS
        print("👤 Création des utilisateurs...")
        
        def hash_pwd(pwd):
            return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

        # On suppose que ton modèle User a bien 'password_hash' (Tier A)
        # Si tu as gardé l'ancien modèle sans hash, change 'password_hash' par 'password' ci-dessous
        admin = User(
            email="admin@imt.test", 
            name="Admin",
            password_hash=hash_pwd("admin"),
            #is_admin=True,
            credits_cents=0
        )
        
        alice = User(
            email="alice@imt.test", 
            name="Alice Vendeuse", 
            password_hash=hash_pwd("alice"),
            credits_cents=0
        )
        
        bob = User(
            email="bob@imt.test", 
            name="Bob Acheteur", 
            password_hash=hash_pwd("bob"),
            credits_cents=10000
        )
        
        db.session.add_all([admin, alice, bob])
        db.session.flush() 

        # 4. CATEGORIES
        print("🏷️  Création des catégories...")
        cat_vetements = Category(name="Vêtements", parent_id=None)
        db.session.add(cat_vetements)
        db.session.flush()

        cat_chaussures = Category(name="Chaussures", parent_id=cat_vetements.id)
        cat_pulls = Category(name="Pulls", parent_id=cat_vetements.id)
        db.session.add_all([cat_chaussures, cat_pulls])
        db.session.flush()

        # 5. ANNONCES
        print("📦 Création des annonces...")
        
        # ICI LA MODIFICATION : On utilise "active" (String) directement
        listing1 = Listing(
            seller_email="alice@imt.test",
            title="Nike Air Max",
            description="Portées deux fois.",
            price_cents=5000,
            shipping_cents=500,
            category_id=cat_chaussures.id,
            status="active"  # <--- String simple
        )
        
        listing2 = Listing(
            seller_email="alice@imt.test",
            title="Pull en laine",
            description="Chaud pour l'hiver.",
            price_cents=3000,
            shipping_cents=400,
            category_id=cat_pulls.id,
            status="active"  # <--- String simple
        )

        db.session.add_all([listing1, listing2])
        db.session.flush()

        # 6. PHOTOS
        print("📸 Ajout des photos...")
        
        # AJOUT DE L'EXTENSION "jpg" POUR CORRIGER L'ERREUR
        p1 = Photo(
            url="https://images.unsplash.com/photo-1542291026-7eec264c27ff", 
            is_thumbnail=True, 
            listing_id=listing1.id,
            extension="jpg"  # <--- L'AJOUT EST ICI
        )
        
        p2 = Photo(
            url="https://images.unsplash.com/photo-1556905055-8f358a7a47b2", 
            is_thumbnail=True, 
            listing_id=listing2.id,
            extension="jpg"  # <--- ET ICI
        )
        
        db.session.add_all([p1, p2])

        db.session.commit()
        print("✅ Terminé ! Base de données prête.")

if __name__ == "__main__":
    init_data()