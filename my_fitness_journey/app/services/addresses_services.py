from app.database.database import db
from app.models.users import User
from app.models.addresses import Address
from app.services.errors import ApiError, NotFoundError, ForbiddenError, UnauthorizedError

class AddressService:
    
    # R: READ - GET /api/addresses
    @staticmethod
    def get_addresses(actor_email: str):
        user = User.query.filter_by(email=actor_email).first()
        if not user:
            raise NotFoundError("Not found")
        
        addresses = Address.query.filter_by(user_email=actor_email).all()
        return [a.to_dict() for a in addresses]

    # C: CREATE - POST /api/addresses
    @staticmethod
    def add_address(data: dict, actor_email: str):
        required_fields = ['line1', 'city', 'postal_code']
        user = User.query.filter_by(email=actor_email).first()
        if not user:
            raise UnauthorizedError("Unauthorized: Missing X-User-Email")
        if not all(field in data for field in required_fields):
            raise ApiError("Missing required address fields.")
        
            
        address = Address(
            user_email=actor_email,
            line1=data['line1'],
            line2=data.get('line2'), # Gère null si absent
            city=data['city'],
            postal_code=data['postal_code']
        )
        db.session.add(address)
        db.session.commit()
        return address.to_dict()


    # U: UPDATE - PUT /api/addresses/{address_id}
    @staticmethod
    def update_address(address_id: int, data: dict, actor_email: str):
        address = Address.query.get(address_id)

        if not address:
            raise NotFoundError("Not found")
            
        # 1. Vérification des droits (l'utilisateur doit être le propriétaire)
        if address.user_email != actor_email:
            raise ForbiddenError("Forbidden: You do not own this address.")

        required_fields = ['line1', 'city', 'postal_code']
        if not all(field in data for field in required_fields):
            raise ApiError("Missing required address fields.")
        
        # 2. Mise à jour  (PUT)
        address.line1 = data['line1']
        address.line2 = data.get('line2') # Met à jour ou met à null
        address.city = data['city']
        address.postal_code = data['postal_code']
        
        db.session.commit()
        return address.to_dict()

    # D: DELETE - DELETE /api/addresses/{address_id}
    @staticmethod
    def delete_address(address_id: int, actor_email: str):
        address = Address.query.get(address_id)
        
        if not address:
            raise NotFoundError("Not found")
            
        # 1. Vérification des droits
        if address.user_email != actor_email:
            raise ForbiddenError("Forbidden: You do not own this address.")

        db.session.delete(address)
        db.session.commit()
        return