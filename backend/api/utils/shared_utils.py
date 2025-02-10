from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional, Tuple
import os
import logging

# to get a string like this run: openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # Default 60 minutes if not set

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    username: Optional[str] = None
    exp: Optional[float] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def check_token_expiration(token: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a token is expired.
    Returns a tuple of (is_expired: bool, error_message: Optional[str])
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        
        if not exp:
            logging.warning("Token has no expiration claim")
            return True, "Token has no expiration"
            
        # Check if token has expired
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            logging.warning("Token has expired")
            return True, "Token has expired"
            
        return False, None
        
    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired (ExpiredSignatureError)")
        return True, "Token has expired"
    except jwt.JWTError as e:
        logging.error(f"Invalid token: {str(e)}")
        return True, f"Invalid token: {str(e)}"
    except Exception as e:
        logging.error(f"Error checking token expiration: {str(e)}")
        return True, f"Error checking token: {str(e)}"

def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate the access token.
    Returns TokenData if valid, None if invalid or expired.
    """
    try:
        # First check if token is expired
        is_expired, error = check_token_expiration(token)
        if is_expired:
            logging.warning(f"Token validation failed: {error}")
            return None
            
        # If not expired, decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        exp: float = payload.get("exp")
        
        if username is None:
            logging.warning("Token has no username")
            return None
            
        return TokenData(username=username, exp=exp)
        
    except JWTError as e:
        logging.error(f"JWT error decoding token: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error decoding token: {str(e)}")
        return None
