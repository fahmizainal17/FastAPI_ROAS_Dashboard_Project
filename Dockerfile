# Use the official Python image from the Docker Hub
FROM python:3.10-slim-bullseye

# Install dependencies
RUN echo "### --- Ubuntu dependencies --- ###" \
    && apt-get update \
    && apt-get install -y \
    g++ \
    cmake \
    unzip \
    curl \
    poppler-utils 

# Set the working directory in the container
WORKDIR /FastAPI_for_Roas

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 80
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
