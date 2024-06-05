# Use the official Python image from the Docker Hub
FROM python:3.10-slim-bullseye

# Set the working directory in the container
WORKDIR /FastAPI_for_Roas_Dashboard_app

# Copy the rest of the application code into the container
COPY app .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["uvicorn", "FastAPI_for_Roas_Dashboard_app.main:app", "--reload","--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
