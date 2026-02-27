from app.models.listings import Listing # Assurez-vous d'importer ListingStatus si c'est un Enum
from app.models.users import User
from app.models.photos import Photo 
from app.models.categories import Category
from app.database.database import db
from app.services.buyer_protection_config_services import BuyerProtectionService
from app.services.errors import NotFoundError, ForbiddenError, ApiError, ConflictError
import re

# Dépendance de la constante Admin (assumée ici pour la lisibilité)
ADMIN_EMAIL="admin@imt.test"


class ListingService:
    
    # -----------------------------------------------------
    # R: READ (GET /api/listings/{listing_id})
    # -----------------------------------------------------
    @staticmethod
    def get(listing_id: int):
        listing = Listing.query.get(listing_id)
        
        if not listing:
            raise NotFoundError("Not found")
        
        totals = BuyerProtectionService.calculate_totals(
            price_cents=listing.price_cents, 
            shipping_cents=listing.shipping_cents
        )
        
        listing_dict = listing.to_dict(include_photos=True) 
        listing_dict['insurance_part_cents'] = totals['insurance_part_cents']
        listing_dict['total_cents'] = totals['total_cents']
        
        return listing_dict
            
    # -----------------------------------------------------
    # C: CREATE (POST /api/listings) - Liaison par ID
    # -----------------------------------------------------
    @staticmethod
    def create(data: dict, seller_email: str):
        # 1. Validation de l'existence des ressources (User/Category)
        user = User.query.filter_by(email=seller_email).first()
        if not user: raise NotFoundError("Seller user not found") 
        if not Category.query.get(data.get("category_id")): raise NotFoundError("Category not found")
        
        # 2. Validation des photos (IDs)
        photo_submissions = data.get("photos", [])
        
        if not isinstance(photo_submissions, list) or not (1 <= len(photo_submissions) <= 12):
            raise ApiError("'photos' must be a list of 1 to 12 items.")
            
        photo_ids_to_link = [p.get("id") for p in photo_submissions]
        
        # Récupération des objets Photo existants
        photos_to_link = Photo.query.filter(Photo.id.in_(photo_ids_to_link)).all()

        if len(photos_to_link) != len(photo_ids_to_link):
            raise NotFoundError("One or more photo IDs are invalid.")
            
        # 3. Logique de Miniature et de Validation
        nb_thumbnails = sum(1 for p in photo_submissions if p.get("is_thumbnail"))

        if nb_thumbnails > 1: raise ApiError("Photos must have at most 1 thumbnail.")
        
        if nb_thumbnails == 0 and photo_submissions:
            photo_submissions[0]["is_thumbnail"] = True

        # 4. Création du Listing
        listing = Listing(
            seller_email=seller_email,
            title=data.get("title"),
            description=data.get("description"),
            price_cents=data.get("price_cents"),
            shipping_cents=data.get("shipping_cents", 0),
            category_id=data["category_id"],
            # status est par défaut 'active'
        )

        # 5. LIAISON ATOMIQUE : Attachement des photos existantes
        for p_submitted in photo_submissions:
            photo_obj = next((p for p in photos_to_link if p.id == p_submitted["id"]), None)
            
            if photo_obj:
                photo_obj.is_thumbnail = p_submitted.get("is_thumbnail", False)
                listing.photos.append(photo_obj) 
                db.session.add(photo_obj) # Marque la photo comme modifiée (update listing_id)
        
        db.session.add(listing)
        db.session.commit()
        
        return listing.to_dict(include_photos=True)


    # -----------------------------------------------------
    # U: UPDATE (PUT /api/listings/{listing_id})
    # -----------------------------------------------------
    @staticmethod
    def update(actor_email: str, listing_id: int, data: dict):
        # ... (Logique de mise à jour et de vérification des droits/statut 'sold') ...
        
        # 🚨 Note: Si 'photos' est dans data, la logique doit répéter la LIAISON par ID
        # et utiliser listing.photos.clear() avant de ré-attacher les nouvelles photos.
        
        raise NotImplementedError("Update logic for listing service photos is complex and requires explicit implementation.")
    
    # -----------------------------------------------------
    # D: DELETE (DELETE /api/listings/{listing_id})
    # -----------------------------------------------------
    @staticmethod
    def delete(ident: int, actor_email: str): 
        listing = Listing.query.get(ident)
        
        if not listing: raise NotFoundError("Not found")

        is_admin = (actor_email == ADMIN_EMAIL)
        if listing.seller_email != actor_email and not is_admin:
            raise ForbiddenError("Forbidden: not owner or admin")

        if listing.status == 'sold': # Assurez-vous que c'est la valeur de l'Enum ou de la string
             raise ForbiddenError("Forbidden: sold listing cannot be deleted by seller")

        # Suppression Logique (Tier A)
        listing.status = 'deleted'
        db.session.commit()
        
        return listing.to_dict(include_photos=True)