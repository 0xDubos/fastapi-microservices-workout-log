import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, SQLModel, Session, create_engine, select
from passlib.context import CryptContext

# Database Setup 
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Security Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Data Models
class UserBase(SQLModel):
    username: str

class UserCreate(UserBase):
    password:str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

# FastAPI App 
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# API Endpoints
@app.post("/users/", response_model=UserBase)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """Creates a new user account."""
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered.")

    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user

@app.get("/users/{user_id}", response_model=UserBase)
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Gets a specific user by their ID."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user