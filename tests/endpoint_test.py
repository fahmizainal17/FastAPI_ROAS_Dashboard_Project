from fastapi.testclient import TestClient
import pytest
from tests.test_main import app  

client = TestClient(app)

# Test the welcome page endpoint
def test_welcome_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to FastAPI For ROAS Dashboard" in response.text

# Test the filter_dataframe endpoint
def test_filter_dataframe():
    sample_data = {
        "data": [
            {"Client Industry": "Tech", "Facebook Page Name": "Tech Innovations", "Country": "USA"},
            {"Client Industry": "Health", "Facebook Page Name": "Health Innovations", "Country": "Canada"}
        ],
        "filter_options": {"Client Industry": "Tech"}
    }
    response = client.post("/filter_dataframe", json=sample_data)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["Client Industry"] == "Tech"

# Test the get_descriptive_stats endpoint
def test_get_descriptive_stats():
    sample_data = {
        "data": [
            {"Cost per Result": 10, "Cost per Mile": 200, "Result Type": "Likes"},
            {"Cost per Result": 20, "Cost per Mile": 300, "Result Type": "Likes"}
        ]
    }
    response = client.post("/get_descriptive_stats", json=sample_data)
    assert response.status_code == 200
    stats = response.json()
    assert 'min_cpr' in stats[0]
    assert 'max_cpr' in stats[0]
    assert stats[0]['min_cpr'] <= stats[0]['max_cpr']

# Add more tests as needed for each endpoint

if __name__ == "__main__":
    pytest.main()
