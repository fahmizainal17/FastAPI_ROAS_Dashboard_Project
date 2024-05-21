from fastapi.testclient import TestClient
import pytest
from tests.test_main import app  
import pandas as pd
import os
from io import StringIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = TestClient(app)

# Test the welcome page endpoint
def test_welcome_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to FastAPI For ROAS Dashboard" in response.text

def test_filter_dataframe_endpoint():
    sample_data = {
        "data": [
            {"Client Industry": "Tech", "Facebook Page Name": "Tech Innovations", "Facebook Page Category": "Business", "Ads Objective": "Awareness", "Start Year": 2020, "Result Type": "Likes", "Country": "USA"},
            {"Client Industry": "Health", "Facebook Page Name": "Health Innovations", "Facebook Page Category": "Medical", "Ads Objective": "Conversion", "Start Year": 2021, "Result Type": "Sales", "Country": "Canada"}
        ],
        "filter_options": {"Client Industry": "Tech"}
    }
    response = client.post("/first_page/filter_dataframe", json=sample_data)
    assert response.status_code == 200
    filtered_data = response.json()
    assert all(item["Client Industry"] == "Tech" for item in filtered_data)

def test_get_descriptive_stats_endpoint():
    sample_data = {
        "data": [
            {"Cost per Result": 10, "Cost per Mile": 200, "Result Type": "Likes"},
            {"Cost per Result": 20, "Cost per Mile": 300, "Result Type": "Likes"}
        ]
    }
    response = client.post("/first_page/get_descriptive_stats", json=sample_data)
    assert response.status_code == 200
    stats = response.json()
    assert 'Min CPR' in stats[0]
    assert 'Max CPR' in stats[0]
    assert stats[0]['Min CPR'] <= stats[0]['Max CPR']

def test_main_endpoint():
    response = client.post("/first_page/main")
    assert response.status_code == 200
    assert len(response.json()) > 0  # Ensure there is at least one valid entry

def test_load_data_endpoint():
    key = os.getenv("OBJECT_NAME_1")
    assert key is not None, "OBJECT_NAME_1 environment variable is not set"
    response = client.get(f"/first_page/load-data/{key}")
    assert response.status_code == 200, f"Failed to load data: {response.status_code}"
    assert "text/csv" in response.headers["content-type"], "Response is not in CSV format"

    # Use StringIO to handle the response content as a file-like object
    csv_content = StringIO(response.content.decode('utf-8'))
    df = pd.read_csv(csv_content)
    assert not df.empty, "DataFrame loaded from endpoint is empty"
    assert 'Campaign ID' in df.columns, "Expected column 'Campaign ID' not found in DataFrame"
    assert 'Result Type' in df.columns, "Expected column 'Result Type' not found in DataFrame"

    # Print the loaded data for verification
    print(df.head())

if __name__ == "__main__":
    pytest.main()
