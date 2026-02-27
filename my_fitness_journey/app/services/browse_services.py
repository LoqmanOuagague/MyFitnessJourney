

from app.models.listings import Listing
from app.models.categories import Category
from app.services.buyer_protection_config_services import BuyerProtectionService
from app.database.database import db
from app.services.errors import ApiError, NotFoundError
from sqlalchemy import or_
from typing import List

class BrowseService:

    @staticmethod
    def _get_descendant_category_ids(category_id: int) -> List[int]:
        """
        Récupère  tous les ID des catégories descendantes
        """
        descendant_ids = set()
        # Commencer avec la catégorie parente comme point de départ pour la recherche d'enfants
        categories_to_check = [category_id]
        
        while categories_to_check:
            parent_id = categories_to_check.pop(0) # Prendre le premier ID à vérifier
            
            # Rechercher tous les enfants directs de ce parent_id
            children = Category.query.filter_by(parent_id=parent_id).all()
            
            for child in children:
                if child.id not in descendant_ids:
                    descendant_ids.add(child.id)
                    categories_to_check.append(child.id) # Ajouter l'enfant pour la vérification future
                    
        return list(descendant_ids)

    @staticmethod
    def get_listings_page(q: str, category_id: int, 
                          min_price_cents: int, max_price_cents: int, 
                          min_total_cents: int, max_total_cents: int, 
                          sort: str, order: str, page: int, page_size: int):
        
        # 1. Base de la requête : Filtrer uniquement les annonces 'active'
        query = Listing.query.filter_by(status='active')
        
        # 2. Logique de Filtrage

        # 2.1. Filtre Texte 'q' (Titre OU Description)
        if q:
            search_term = f"%{q}%"         
            query = query.filter(
                or_(                                             #cherche n'importe quelle phrase contenant la chaine de caracteres q dans title ou description
                    Listing.title.ilike(search_term),
                    Listing.description.ilike(search_term)
                )
            )

        # 2.2. Filtre Catégorie (ID + Descendants)
        if category_id:
            # Récupère tous les ID qui doivent être inclus
            target_ids = BrowseService._get_descendant_category_ids(category_id)
            target_ids.append(category_id) # Inclure la catégorie principale elle-même
            query = query.filter(Listing.category_id.in_(target_ids))

        # 2.3. Filtres Prix (price_cents)
        if min_price_cents is not None:
            query = query.filter(Listing.price_cents >= min_price_cents)
        if max_price_cents is not None:
            query = query.filter(Listing.price_cents <= max_price_cents)

        # 3. Tri (Tri par Total et Filtrage par Total sont gérés après le calcul)
        
        # Tri primaire sur 'price_cents' (plus efficace en DB)
        sort_column = Listing.price_cents
        
        if order == 'desc':
            query = query.order_by(sort_column.desc(), Listing.id.asc()) # Tier: "ties broken by id ASC"
        else:                                                            # le deuxieme critere d'ordre (listing.id) n'est mis en places que lorsque deux ou plus de listings ont le meme price_cents
            query = query.order_by(sort_column.asc(), Listing.id.asc())

        # 4. Pagination
        paginated_results = query.paginate(page=page, per_page=page_size, error_out=False)
        
        # 5. Calcul des Totaux (Post-traitement)
        
        try:
            config = BuyerProtectionService.get_config()
        except NotFoundError:
            # Si la configuration n'existe pas, on lève une erreur 500 ou on utilise 0 (Mieux : 500)
            raise ApiError("Internal Error: Buyer Protection configuration missing.")
             
        items_with_totals = []
        
        for listing in paginated_results.items:
            
            # Calculer les totaux en utilisant la configuration courante
            totals = BuyerProtectionService.calculate_totals(
                price_cents=listing.price_cents,
                shipping_cents=listing.shipping_cents,
                config_data=config
            )
            
            # Construire l'objet ListingWithTotals
            listing_dict = listing.to_dict(include_photos=True) # On inclut les photos pour la conformité
            listing_dict['insurance_part_cents'] = totals['insurance_part_cents']
            listing_dict['total_cents'] = totals['total_cents']
            
            # 5.1. Filtres Totaux (Appliqué côté Python pour contourner l'inefficacité SQL)
            if min_total_cents is not None and listing_dict['total_cents'] < min_total_cents:
                continue
            if max_total_cents is not None and listing_dict['total_cents'] > max_total_cents:
                continue
                 
            items_with_totals.append(listing_dict)
            
        # 6. Tri final sur le total si demandé (pour compenser l'inefficacité SQL)
        if sort == 'total':
            # On trie la liste Python (plus lent, mais nécessaire si le tri en DB n'est pas possible)
            items_with_totals.sort(key=lambda x: x['total_cents'], reverse=(order == 'desc'))

        return {
            "items": items_with_totals,
            "total_items": paginated_results.total, # NOTE: Ce total inclut les items filtrés en 5.1
            "page": page,
            "page_size": page_size
        }