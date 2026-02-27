from app.models.categories import Category
from app.database.database import db

from app.services.errors import ConflictError
from app.models.categories import Category
from app.database.database import db


class CategoryService:
    @staticmethod
    def get_all():
        cats = Category.query.all()
        return [c.to_dict() for c in cats]

    @staticmethod
    def create(data: dict):

        #  Vérification des clés autorisées
        allowed_keys_sets = [{"name", "parent_id"}, {"name"}]
        if set(data.keys()) not in allowed_keys_sets:
            raise ValueError(f"Invalid keys in data. Expected: {allowed_keys_sets}, got: {set(data.keys())}")

        # verification du type du parent_id
        parent_id=data.get("parent_id")
        if parent_id is not None: 
            if not isinstance(data["parent_id"],int) or data["parent_id"]<1:
                raise ValueError("parent_id must be  integer & positive ") 
            
            # Vérification existence parent
            if not Category.query.get(parent_id):
                 raise ValueError("Parent category not found")
            
        #mise a jour de data
        if set(data.keys())=={"name"}:
            data.update({"parent_id": None})

        # Vérification si la catégorie existe déjà
        cats = Category.query.filter_by(parent_id=data["parent_id"]).all()
        if cats != [] :
            for cat in cats:
                if cat.name.lower() == data["name"].lower():
                    raise ValueError("category already exists")

        cat = Category(
            name=data["name"],
            parent_id=data["parent_id"],
        )
        db.session.add(cat)
        db.session.commit()
        return cat.to_dict()

    

    @staticmethod
    def delete(identifiant: int):
        cat = Category.query.filter_by(id=identifiant).first()
        
        if not cat:
            raise ValueError("category not found") # Sera mappé à 404

        # 1. Vérification des enfants directs (via le backref 'children')
        # 2. Vérification des annonces rattachées directement (via le db.relationship 'listings')
        
        if cat.children or cat.listings: 
            # Si l'une ou l'autre des listes n'est pas vide (contient au moins un élément),
            # on lève l'erreur 409.
            # NOTE : Le Tier A exige aussi la vérification des listings dans les DESCENDANTS. 
            # Pour l'étape minimale, nous nous concentrons sur les listings DIRECTS. 
            # La vérification des descendants nécessiterait une requête récursive plus complexe.
            raise ConflictError("Conflict: category has children or listings") 

        # Si les vérifications passent, on supprime.
        db.session.delete(cat)
        db.session.commit()
        return