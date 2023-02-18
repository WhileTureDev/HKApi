from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db, Users
from .schemas import UserCreate, Token, TokenData, User, UserInDB
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt

router = APIRouter()
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "849b55fe474e03f125c5c27529aa9446b3c0f2c4381e9cc0416d0f52cfb422fc"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, password):
    return pwd_context.verify(plain_password, password)


# Authenticate user and return access token
def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


# def get_user(db, username: str):
#     if username in db:
#         user_dict = db[username]
#         return UserInDB(**user_dict)

def get_user(db: Session, username: str):
    return db.query(Users).filter(Users.username == username).first()


# Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Users = Depends(get_current_user)):
    if current_user.disabled:
        print(f"Current get_current_active_user: {current_user}")
        raise HTTPException(status_code=400, detail="Inactive user")
    print(f"Current active user: {current_user}")
    return User(username=current_user.username, full_name=current_user.full_name, email=current_user.email)


# Create a new user
@router.post("/register", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    password = pwd_context.hash(user.password)
    created_at = datetime.utcnow()
    db_user = Users(username=user.username, full_name=user.full_name, email=user.email, password=password,
                    created_at=created_at)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User(username=db_user.username, full_name=db_user.full_name, email=db_user.email)


# Authenticate user and return access token
# @router.post("/login", response_model=Token)
# def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.email == form_data.username).first()
#     if not db_user:
#         raise HTTPException(status_code=400, detail="Incorrect email or password")
#     if not pwd_context.verify(form_data.password, db_user.password):
#         raise HTTPException(status_code=400, detail="Incorrect email or password")
#
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token_payload = {
#         "sub": db_user.email,
#         "exp": datetime.utcnow() + access_token_expires
#     }
#     access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)
#
#     return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
