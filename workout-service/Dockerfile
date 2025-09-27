FROM python:3.11-slim

# Creates fold in our container and assigns it as current location
WORKDIR /app

# Copies requirements folder into our container
COPY requirements.txt .

# Runs pip to install necessary requirements
RUN pip install -r requirements.txt

# Copies the rest of our application code into the container.
COPY . .

# The command to run when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]