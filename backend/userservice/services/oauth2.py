from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User

# Define a custom exception for user not found
class UserNotFoundException(Exception):
    def __init__(self, message="User not found", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


# Create a new user (asynchronous)
async def create_user(db: AsyncSession, user: dict):
    # Set role dynamically
    db_user = User(
        firstname=user['given_name'],
        lastname=user['family_name'],
        picture=user['picture'],
        email=user['email'],
        role=user['role'],  # Set the role dynamically
        active=user['email_verified']
    )
    
    db.add(db_user)
    await db.commit()  # Commit the transaction asynchronously
    await db.refresh(db_user)  # Refresh to get updated info (e.g., ID after commit)
    return db_user
