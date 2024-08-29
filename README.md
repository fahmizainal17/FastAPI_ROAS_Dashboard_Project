# **📊 FastAPI ROAS Dashboard Project**

---

## **Technologies Used 🔧**

<div>
    <h1 style="text-align: center;">Backend API Development with Python, FastAPI, and AWS</h1>
    <img style="text-align: left" src="https://img.icons8.com/color/48/000000/python.png" width="10%" alt="Python Logo" />
    <img style="text-align: left" src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" width="10%" alt="FastAPI Logo" />
    <img style="text-align: left" src="https://img.icons8.com/color/48/000000/docker.png" width="10%" alt="Docker Logo" />
    <img style="text-align: left" src="https://img.icons8.com/color/48/000000/amazon-web-services.png" width="10%" alt="AWS Logo" />
</div>
<br>

![Python](https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)

---

## **📋 Table of Contents**

1. [Overview](#overview)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Running the Application](#running-the-application)
5. [Endpoints](#endpoints)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [License](#license)
9. [Contact](#contact)

---

## **1. Overview 📖**

The **FastAPI ROAS Dashboard Project** is designed to create a backend API service for a Return on Ad Spend (ROAS) dashboard. The project utilizes FastAPI, an efficient and high-performance web framework for building APIs in Python. The backend service is designed to handle various tasks such as filtering campaign data, calculating descriptive statistics, and forecasting campaign performance based on budget allocation. The project separates the backend functionality from the frontend, enabling a streamlined development and testing process.

---

## **2. Features ✨**

- **Data Filtering**: Filter campaign data based on various criteria, with support for pagination.
- **Descriptive Statistics**: Calculate key performance metrics such as Cost Per Result (CPR) and Cost Per Mile (CPM) across different campaigns.
- **Forecasting**: Predict campaign performance based on budget allocation and distribution.
- **AWS S3 Integration**: Load and manage data directly from AWS S3 storage.
- **Robust Testing**: Comprehensive testing of endpoints and backend functionality using Pytest.

---

## **3. Project Structure 📂**

```
FastAPI_ROAS_Dashboard_Project/
│
├── app/
│   ├── routers/
│   │   ├── load_exp_data_utils.py
│   │   ├── miscellaneous_utils.py
│   │   └── Autoforecaster_module.py
│   └── __init__.py
│
├── tests/
│   ├── .request_body
│   ├── routers/
│   ├── __init__.py
│   ├── backend_test.py
│   └── endpoint_test.py
│   └── test_main.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── LICENSE
└── README.md
```

This structure organizes the backend logic under `app/`, with routers for handling specific functionalities. The `tests/` directory includes test cases for validating both backend and endpoint functionalities, ensuring robust performance.

---

## **4. Getting Started 🚀**

### **Prerequisites**

- Python 3.8+
- FastAPI
- Docker (optional, for containerization)
- AWS credentials with access to S3 (if loading data from S3)

### **Installation**

1. **Clone the Repository**

   ```bash
   git clone https://github.com/fahmizainal17/FastAPI_ROAS_Dashboard_Project.git
   cd FastAPI_ROAS_Dashboard_Project
   ```

2. **Set Up a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**

   Create a `.env` file in the root directory and configure your AWS credentials and any other required environment variables:

   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   BUCKET_NAME=your_bucket_name
   ```

### **Running the Application**

1. **Start the FastAPI Application**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be accessible at `http://127.0.0.1:8000`.

2. **Access the Swagger UI**

   You can access the Swagger UI for testing the endpoints at `http://127.0.0.1:8000/docs`.

---

## **5. Endpoints 📡**

1. **Filter Dataframe with Pagination**

   - **Endpoint**: `/filter_dataframe`
   - **Method**: POST
   - **Description**: Filters campaign data based on provided options and paginates the results.
   - **Request Body**:
     ```json
     {
       "data": [...],
       "filter_options": {...},
       "pagination": {
         "page": 1,
         "size": 10
       }
     }
     ```

2. **Get Descriptive Stats**

   - **Endpoint**: `/get_descriptive_stats`
   - **Method**: POST
   - **Description**: Calculates key performance metrics (CPR, CPM) for different campaigns.
   - **Request Body**:
     ```json
     {
       "data": [...]
     }
     ```

3. **Get Forecast by Value**

   - **Endpoint**: `/get_forecast_by_value`
   - **Method**: POST
   - **Description**: Forecasts campaign performance (impressions, results) based on budget allocation.
   - **Request Body**:
     ```json
     {
       "data": [...],
       "budget": 10000,
       "distribution": {
         "Result Type 1": 50,
         "Result Type 2": 50
       }
     }
     ```

4. **Load Data from AWS S3**

   - **Endpoint**: `/load-data/{key}`
   - **Method**: GET
   - **Description**: Loads data from AWS S3 bucket using the provided key.

---

## **6. Testing 🧪**

1. **Run Tests**

   Run the test suite using Pytest to ensure all functionalities are working correctly:

   ```bash
   pytest tests/
   ```

   The tests include both backend and endpoint tests to ensure the API functions correctly.

---

## **7. Deployment 🚢**

- **Docker**: The project includes a `Dockerfile` for containerization. You can build and run the Docker container using:

   ```bash
   docker build -t fastapi_roas_dashboard .
   docker run -p 8000:8000 fastapi_roas_dashboard
   ```

- **AWS**: The application can be deployed on AWS using services like ECS or Lambda, with proper configuration for environment variables and S3 access.

---

## **8. License 📜**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## **9. Contact 📬**

For any inquiries, please contact Fahmi Zainal at [LinkedIn](https://www.linkedin.com/in/fahmizainal17).

---
