
class ConflictError(ValueError):
    """Erreur levée lorsque la requête est en conflit avec l'état actuel (par exemple, suppression impossible)."""
    pass

class NotFoundError(ValueError):
    """Mappé à 404 Not Found"""
    pass

class ForbiddenError(ValueError):
    """Mappé à 403 Forbidden"""
    pass
class ApiError(ValueError):
    """Mappé à 400 ApiError"""
class UnauthorizedError(ValueError):
    """Mappé à 401 ApiError"""
    
