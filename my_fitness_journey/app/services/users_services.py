from app.models.users import User
from app.database.database import db
import re
from app.models.listings import Listing
import hashlib


class UserService:
    @staticmethod
    def get_all():
        users = User.query.all()
        return [u.to_dict() for u in users]

    @staticmethod
    def create(data: dict):
        #  Vérification des clés autorisées
        allowed_keys_sets = [
            {"email", "password", "credits_cents", "name"}, 
            {"email", "password", "credits_cents"}
        ]
        if set(data.keys()) not in allowed_keys_sets: 
            raise ValueError(f"Invalid keys in data. Expected: {allowed_keys_sets}, got: {set(data.keys())}")
        
        #Verification du bon format de l'email
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(pattern, data["email"]):
            raise ValueError("Invalid email format")
        
        #verification que le credit est un nombre : 
        if not isinstance(data["credits_cents"], int) or data["credits_cents"] < 0 : 
            raise ValueError("credits_cents must be  integers & positive ")
        
        # Vérifie si l'utilisateur existe déjà
        existing = User.query.filter_by(email=data["email"]).first()
        if existing:
            raise ValueError("User already exists")
        
        raw_password = data.get("password")
        if not raw_password:
             raise ValueError("Password is required")
             
        # On crypte le mot de passe avant de le stocker
        pwd_hash = hashlib.sha256(raw_password.encode('utf-8')).hexdigest()

        user = User(
            email=data["email"],
            name=data["name"],
            credits_cents=data.get("credits_cents", 0),
            #is_admin=data.get("is_admin", False)
            password_hash=pwd_hash
        )
        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    def delete(email: str):
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("User not found")
        else:
            # On sélectionne toutes les annonces actives de cet utilisateur
            listings_to_update = Listing.query.filter_by(
            seller_email=email,
            status='active'
            ).all()
        
        # 2. On change le statut de chacune à 'deleted'
        for listing in listings_to_update:
            listing.status = 'deleted'
            db.session.add(listing)

        db.session.delete(user)
        db.session.commit()
        return {"message": f"User {email} deleted successfully"}
