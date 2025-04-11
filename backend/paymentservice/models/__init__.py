# models/__init__.py
from .currency import Currency
from .payments import Payment
# import other models too...

from core.database import Base  # or wherever your Base is defined
