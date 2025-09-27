import requests
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, SQLModel, Session, create_engine, select

# Database Setup
engine = create_engine("sqlite:///./workouts.db", echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Data Models
class WorkoutBase(SQLModel):
    name: str
    sets: int
    reps: int
    weight: int
    user_id: int # Assigns workout to a user

class WorkoutCreate(WorkoutBase):
    pass

class Workout(WorkoutBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# Helper Funtion for Service-to-Servce Communication
def user_exists(user_id: int) -> bool:
    """Checks if a user exists by calling the user-service."""
    try:
        response = requests.get(f"http://127.0.0.1:8000/users/{user_id}")
        # Return True if the user-service says "OK" (status code 200)
        return response.status_code == 200
    except requests.ConnectionError:
        # In case we can't connect to the user-service at all
        return False

# FastAPI App
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# API Endpoints
@app.post("/workouts/", response_model=Workout)
def create_workout(workout: WorkoutCreate, session: Session = Depends(get_session)):
    """Creates a new workout, but only if the user exists"""
    if not user_exists(workout.user_id):
        raise HTTPException(status_code=404, detail=f"User with id {workout.user_id} not found.")

    db_workout = Workout.model_validate(workout)
    session.add(db_workout)
    session.commit()
    session.refresh(db_workout)

    return db_workout

@app.get("/workouts/", response_model=list[Workout])
def get_workouts(session: Session = Depends(get_session)):
    """Gets all workouts."""
    workouts = session.exec(select(Workout)).all()
    return workouts