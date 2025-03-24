from pydantic_settings import BaseSettings, SettingsConfigDict  # Import for configuration management with Pydantic
from typing import Annotated, Literal, Any  # Various typing utilities for annotations
from pydantic import (
    AnyUrl,  # Import for handling URLs in validation
    BeforeValidator,  # Import for custom validators before setting the value
    computed_field,  # Import for computed fields (i.e., derived values)
    PostgresDsn,  # Import for Postgres DSN type
    Field  # Field validation tool in Pydantic
)
from pydantic_core import MultiHostUrl  # Import for handling multi-host URLs (not used in this example)


# Function to parse CORS origins, handling both string and list types
# This function will parse a comma-separated string into a list of strings
def parse_cors(v: Any) -> list[list[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]  # Split string into a list of URLs
    elif isinstance(v, (list, str)):  # If input is already a list or string
        return v  # Return as is
    raise ValueError(v)  # If the input is neither, raise a ValueError


class Settings(BaseSettings):
    """
    This class defines all the settings that are required for your application.
    It uses Pydantic’s BaseSettings class to read from environment variables or .env file.
    """
    
    # Configuration for the environment file.
    # This tells Pydantic to read variables from a .env file and ignore empty ones.
    model_config = SettingsConfigDict(env_file='.env', env_ignore_empty=True, extra="ignore")
    
    # Basic settings like domain and environment.
    DOMAIN: str = 'localhost'  # The domain or hostname (default: 'localhost')
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"  # Specifies which environment we're running (default: 'local')

    REDIS_HOST: str = 'localhost'
    REDIS_PORT: str = '6379'
    # PostgreSQL settings
    POSTGRESQL_USER: str  # The username for PostgreSQL
    POSTGRESQL_PASSWORD: str  # The password for PostgreSQL
    POSTGRESQL_SERVER: str  # The server where PostgreSQL is hosted
    POSTGRESQL_PORT: int  # The port PostgreSQL is using (default is usually 5432)
    POSTGRESQL_DB: str  # The name of the PostgreSQL database

    # SQLite settings (fallback to SQLite for local development)
    SQLITE_DB_PATH: str = 'db1.db'  # Default path for the SQLite database

    # CORS settings (for allowing specific origins to access the API)
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []  # Can be a list of URLs or a comma-separated string of allowed CORS origins
    
    # Google OAuth settings (client credentials for Google authentication)
    GOOGLE_CLIENT_ID: str ='' # The Google OAuth client ID
    GOOGLE_CLIENT_SECRET: str ='' # The Google OAuth client secret
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/users/login/google/callback"  # Default redirect URI (should be changed to frontend URL in production)

    # Secret key for cryptography or JWT encoding/decoding
    SECRET_KEY: str = 'django-insecure-i-i^&f9-=cdt+k478)**l!uy2olm)&24&_(-bqo&1+=oh5^5pu'
    
    @computed_field
    @property
    def server_host(self) -> str:
        """
        Dynamically computes the server host URL depending on the environment.
        - In 'local' environment, it returns a 'http://' URL.
        - In 'staging' or 'production', it returns a 'https://' URL.
        """
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"  # Local environment uses HTTP
        return f"https://{self.DOMAIN}"  # Production/staging environments use HTTPS

    @computed_field  # Type: ignore[misc]  # Ignore type checking for this field (Pydantic allows this)
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Based on the environment, return the appropriate database URI.
        Supports both SQLite for local development and PostgreSQL for production or staging.
        """
        if self.ENVIRONMENT == "local":
            # Use SQLite when in local environment
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"  # SQLite URI
        elif self.ENVIRONMENT in ["staging", "production"]:
            # Use PostgreSQL in production or staging environments
            return f"postgresql+asyncpg://{self.POSTGRESQL_USER}:{self.POSTGRESQL_PASSWORD}" \
                   f"@{self.POSTGRESQL_SERVER}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DB}"  # PostgreSQL URI
        else:
            raise ValueError("Unsupported environment for database connection")  # Raise an error for unsupported environments
    

# Initialize settings by reading from environment or .env file
settings = Settings()
