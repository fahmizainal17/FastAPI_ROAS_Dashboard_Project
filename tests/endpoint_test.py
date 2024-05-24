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

@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)


def test_load_data_endpoint(test_client):
    key = os.getenv("OBJECT_NAME_1")
    print(f"OBJECT_NAME_1: {key}")  # Print the key for debugging
    assert key is not None, "OBJECT_NAME_1 environment variable is not set"
    
    response = test_client.get(f"/first_page/load-data/{key}")
    print(f"Response status code: {response.status_code}")  # Print status code for debugging
    print(f"Response content: {response.content[:100]}")  # Print first 100 bytes of response content for debugging
    
    assert response.status_code == 200, f"Failed to load data: {response.status_code}"
    assert "application/octet-stream" in response.headers["content-type"], "Response is not in the expected format"
    
    # Load the content into a DataFrame
    parquet_content = BytesIO(response.content)
    df = pd.read_parquet(parquet_content)
    
    assert not df.empty, "DataFrame loaded from endpoint is empty"
    assert 'Campaign ID' in df.columns, "Expected column 'Campaign ID' not found in DataFrame"
    assert 'Result Type' in df.columns, "Expected column 'Result Type' not found in DataFrame"

    # Print the loaded data for verification
    print(df.head())

if __name__ == "__main__":
    pytest.main()