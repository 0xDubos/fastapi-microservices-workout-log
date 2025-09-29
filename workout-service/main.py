import requests
import os
from dotenv import load_dotenv
from typing import Optional, Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import Field, SQLModel, Session, create_engine, select

load_dotenv() # Load the .env file

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Looks for our token
security_scheme = HTTPBearer()

# Database Setup
engine = create_engine("sqlite:///./workouts.db", echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Data Models
class WorkoutBase(SQLModel):
    # Fields the user provides
    name: str
    sets: int
    reps: int
    weight: int

class WorkoutCreate(WorkoutBase):
    # Creates new workout
    pass

class Workout(WorkoutBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_username: str # Stores owner's username

# Helper Funtions
def user_exists(user_id: int) -> bool:
    """Checks if a user exists by calling the user-service."""
    try:
        response = requests.get(f"http://127.0.0.1:8000/users/{user_id}")
        # Return True if the user-service says "OK" (status code 200)
        return response.status_code == 200
    except requests.ConnectionError:
        # In case we can't connect to the user-service at all
        return False
    
def get_current_user(token: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Decodes the token to get the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Use token.credentials to get the raw string
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # If the wristband is valid, the bouncer returns the username
    return username

# FastAPI App
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# API Endpoints
@app.post("/workouts/", response_model=Workout)
def create_workout(
    workout: WorkoutCreate,
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user) 
    ):
    """Creates a new workout for the currently logged-in user."""

    # Creates new Workout object, adding the owner's username from the token
    db_workout = Workout(
        name=workout.name,
        sets=workout.sets,
        reps=workout.reps,
        weight=workout.weight,
        owner_username=current_user  # Securely assign ownership
    )

    session.add(db_workout)
    session.commit()
    session.refresh(db_workout)
    return db_workout

@app.get("/workouts/", response_model=list[Workout])
def get_workouts(
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user) 
    ):
    """Gets all workouts for the currently logged-in user."""

    # Query to filter by the owner
    statement = select(Workout).where(Workout.owner_username == current_user)
    results = session.exec(statement)
    workouts = results.all()
    return workouts