from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.userModel import User
from ..schemas.userSchema import UserCreate, User as UserSchema
from ..utils.database import get_db

router = APIRouter()


@router.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
