# models/__init__.py
from .user import User, Address, ApiKey
from .vehicle import Vehicle, VehicleType
# import other models too...

from core.database import Base  # or wherever your Base is defined
