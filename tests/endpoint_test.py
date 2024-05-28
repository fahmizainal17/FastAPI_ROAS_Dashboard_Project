from fastapi.testclient import TestClient
import pytest
from tests.test_main import app  
import pandas as pd
import os
from io import BytesIO
from dotenv import load_dotenv
from tests.routers.test_autoforecaster_module import filter_dataframe, get_descriptive_stats, FilterInput, get_storage_config, load_campaigns_df, get_forecast_by_value
from tests.routers.load_exp_data_utils import ImportDataS3, load_clients_df, load_roas_df, load_campaigns_df, load_adsets_df, convert_df, load_feedback_form 
from tests.routers.miscellaneous_utils import round_to_two_decimal_places_with_min 

# Load environment variables from .env file
load_dotenv()

client = TestClient(app)

def test_filter_dataframe_endpoint():
    sample_data1 = {
        "data": [
            {"Client Industry": "Tech", "Facebook Page Name": "Tech Innovations", "Facebook Page Category": "Business", "Ads Objective": "Awareness", "Start Year": 2020, "Result Type": "Likes", "Country": "USA"},
            {"Client Industry": "Health", "Facebook Page Name": "Health Innovations", "Facebook Page Category": "Medical", "Ads Objective": "Conversion", "Start Year": 2021, "Result Type": "Sales", "Country": "Canada"}
        ],
        "filter_options": {"Client Industry": "Tech"}
    }
    response = client.post("/first_page/filter_dataframe", json=sample_data1)
    assert response.status_code == 200
    filtered_data = response.json()
    assert all(item["Client Industry"] == "Tech" for item in filtered_data)

def test_get_descriptive_stats_endpoint():
    sample_data2 = {
        "data": [
            {"Result Type": "Likes", "Min CPM": 200.0, "Median CPM": 220.0, "Max CPM": 240.0, "Min CPR": 10.0, "Median CPR": 12.0, "Max CPR": 14.0},
            {"Result Type": "Likes", "Min CPM": 300.0, "Median CPM": 320.0, "Max CPM": 340.0, "Min CPR": 20.0, "Median CPR": 22.0, "Max CPR": 24.0}
        ]
    }
    response = client.post("/first_page/get_descriptive_stats", json=sample_data2)
    assert response.status_code == 200
    stats = response.json()
    assert 'Min CPR' in stats[0]
    assert 'Max CPR' in stats[0]
    assert stats[0]['Min CPR'] <= stats[0]['Max CPR']


@pytest.fixture
def sample_data_descriptive2():
    data = {
        'Result Type': ['Likes', 'Sales', 'Likes', 'Comments'],
        'Min CPM': [200.0, 300.0, 250.0, 350.0],
        'Median CPM': [220.0, 320.0, 270.0, 370.0],
        'Max CPM': [240.0, 340.0, 290.0, 390.0],
        'Min CPR': [10.0, 20.0, 15.0, 25.0],
        'Median CPR': [12.0, 22.0, 18.0, 28.0],
        'Max CPR': [14.0, 24.0, 21.0, 31.0]
    }
    return pd.DataFrame(data)

def test_get_forecast_by_value_endpoint(sample_data_descriptive2):
    budget = 1000
    distribution = {
        'Likes': 40,
        'Sales': 30,
        'Comments': 30
    }

    # Prepare the input data as a dictionary
    input_data = {
        "data": sample_data_descriptive2.to_dict(orient='records'),
        "budget": budget,
        "distribution": distribution
    }

    # Send the POST request to the endpoint
    response = client.post("/first_page/get_forecast_by_value", json=input_data)
    assert response.status_code == 200, f"Failed to get forecast by value: {response.status_code}"
    
    result = response.json()

    # Check that the result is not empty
    assert len(result) > 0, "The result is empty"

    # Check that the expected columns are in the result
    expected_columns = [
        'Result Type',
        'Ad Spent',
        'Max Impressions',
        'Median Impressions',
        'Min Impressions',
        'Max Results',
        'Median Results',
        'Min Results'
    ]
    assert all(column in result[0] for column in expected_columns), "Expected columns not found in the result"

@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)

def test_load_data_endpoint(test_client):
    key = os.getenv("OBJECT_NAME_1")
    assert key is not None, "OBJECT_NAME_1 environment variable is not set"
    
    response = test_client.get(f"/first_page/load-data/{key}")
    assert response.status_code == 200, f"Failed to load data: {response.status_code}"
    assert "application/octet-stream" in response.headers["content-type"], "Response is not in the expected format"
    
    # Load the content into a DataFrame
    parquet_content = BytesIO(response.content)
    df = pd.read_parquet(parquet_content)
    
    assert not df.empty, "DataFrame loaded from endpoint is empty"
    assert 'Campaign ID' in df.columns, "Expected column 'Campaign ID' not found in DataFrame"
    assert 'Result Type' in df.columns, "Expected column 'Result Type' not found in DataFrame"


def test_main_endpoint():
    df_unfiltered = load_campaigns_df()
    print("df_unfiltered")
    print(df_unfiltered.json())  # Debugging statement to inspect the DataFrame

    filter_input = {
        "data": df_unfiltered.to_dict(orient='records'),
        "filter_options": {"Client Industry": "Tech"}
    }
    response = client.post("/first_page/main", json=filter_input)
    assert response.status_code == 200
    print("filtered_df")
    filtered_df = response.json()
    print(filtered_df)  # Debugging statement to inspect the filtered DataFrame
    assert filtered_df is not None
    assert len(filtered_df) > 0

if __name__ == "__main__":
    pytest.main()
