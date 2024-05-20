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

# Setup directory
RUN echo "### --- Directory setup --- ###" \
    && mkdir /app
WORKDIR /app
COPY ./app .

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Change directory to root
WORKDIR /

# Expose port 80
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "tests.test_main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
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

# Setup directory
RUN echo "### --- Directory setup --- ###" \
    && mkdir /app
WORKDIR /app
COPY ./app .

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Change directory to root
WORKDIR /

# Expose port 80
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "tests.test_main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
