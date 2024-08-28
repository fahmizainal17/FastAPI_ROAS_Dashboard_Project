# **FastAPI ROAS Dashboard Project**

## **Overview**
The **FastAPI ROAS Dashboard Project** is designed to create a backend API service for a Return on Ad Spend (ROAS) dashboard. The project utilizes FastAPI, an efficient and high-performance web framework for building APIs in Python. The backend service is designed to handle various tasks such as filtering campaign data, calculating descriptive statistics, and forecasting campaign performance based on budget allocation. The project separates the backend functionality from the frontend, enabling a streamlined development and testing process.

## **Features**
- **Data Filtering**: Filter campaign data based on various criteria, with support for pagination.
- **Descriptive Statistics**: Calculate key performance metrics such as Cost Per Result (CPR) and Cost Per Mile (CPM) across different campaigns.
- **Forecasting**: Predict campaign performance based on budget allocation and distribution.
- **AWS S3 Integration**: Load and manage data directly from AWS S3 storage.
- **Robust Testing**: Comprehensive testing of endpoints and backend functionality using Pytest.

## **Project Structure**

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

## **Getting Started**

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
   - Create a `.env` file in the root directory and configure your AWS credentials and any other required environment variables:

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

### **Endpoints**

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

### **Testing**

1. **Run Tests**

   ```bash
   pytest tests/
   ```

   The tests include both backend and endpoint tests to ensure the API functions correctly.

### **Deployment**

- **Docker**: The project includes a `Dockerfile` for containerization. You can build and run the Docker container using:

   ```bash
   docker build -t fastapi_roas_dashboard .
   docker run -p 8000:8000 fastapi_roas_dashboard
   ```

- **AWS**: The application can be deployed on AWS using services like ECS or Lambda, with proper configuration for environment variables and S3 access.

### **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **Contact**

For any inquiries, please contact Fahmi Zainal at [LinkedIn](https://www.linkedin.com/in/fahmizainal17).

---
