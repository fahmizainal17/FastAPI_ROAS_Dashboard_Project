from fastapi.testclient import TestClient
import pytest
from tests.test_main import app  
from unittest.mock import patch
import pandas as pd
from tests.routers.test_autoforecaster_module import load_campaigns_df_mock
import os

client = TestClient(app)

# Test the welcome page endpoint
def test_welcome_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to FastAPI For ROAS Dashboard" in response.text

# Test the filter_dataframe endpoint
def test_filter_dataframe_endpoint():
    sample_data = {
        "data": [
            {"Client Industry": "Tech", "Facebook Page Name": "Tech Innovations", "Country": "USA"},
            {"Client Industry": "Health", "Facebook Page Name": "Health Innovations", "Country": "Canada"}
        ],
        "filter_options": {"Client Industry": "Tech"}
    }
    response = client.post("/first_page/filter_dataframe", json=sample_data)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["Client Industry"] == "Tech"

# Test the get_descriptive_stats endpoint
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

# Test the main endpoint
def test_main():
    with patch('tests.routers.test_autoforecaster_module.load_campaigns_df', side_effect=load_campaigns_df_mock) as mock_load:
        response = client.post("/first_page/main")
        assert response.status_code == 200
        assert len(response.json()) == 2


def test_load_data():
    # Mock environment variables
    with patch.dict(os.environ, {
        "STORAGE_NAME": "fake_storage_name",
        "STORAGE_ACCOUNT_KEY": "fake_storage_key"
    }):
        # Mock the importDataBlobStorage.load_df method to avoid actual I/O operations
        with patch('tests.routers.test_autoforecaster_module.importDataBlobStorage.load_df') as mock_load_df:
            # Mock return value as a DataFrame, not a list
            mock_load_df.return_value = pd.DataFrame({
                "data": ["data1", "data2"]
            })
            
            # Create a test client
            response = client.get("/first_page/load-data/test_blob")

            # Validate the response
            assert response.status_code == 200
            assert response.json() == [{"data": "data1"}, {"data": "data2"}]


if __name__ == "__main__":
    pytest.main()