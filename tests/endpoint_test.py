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
            {
                "Start_Date": "2023-01-01",
                "Stop_Date": "2023-01-31",
                "Client_Industry": "Tech",
                "Facebook_Page_Name": "Tech Innovations",
                "Facebook_Page_Category": "Business",
                "Ads_Objective": "Awareness",
                "Amount_Spent": 1000.0,
                "Impressions": 100000,
                "Reach": 50000,
                "Result_Type": "Likes",
                "Total_Results": 1000,
                "Cost_per_Result": 1.0,
                "Cost_per_Mile": 10.0,
                "Campaign_Name": "Tech Campaign",
                "Campaign_ID": 12345,
                "Account_ID": "abc123",
                "Company_Name": "Tech Innovations Inc",
                "Country": "USA",
                "Start_Year": 2023,
                "Start_Month": "January"
            },
            {
                "Start_Date": "2023-02-01",
                "Stop_Date": "2023-02-28",
                "Client_Industry": "Health",
                "Facebook_Page_Name": "Health Innovations",
                "Facebook_Page_Category": "Medical",
                "Ads_Objective": "Conversion",
                "Amount_Spent": 2000.0,
                "Impressions": 200000,
                "Reach": 100000,
                "Result_Type": "Sales",
                "Total_Results": 2000,
                "Cost_per_Result": 1.0,
                "Cost_per_Mile": 10.0,
                "Campaign_Name": "Health Campaign",
                "Campaign_ID": 67890,
                "Account_ID": "def456",
                "Company_Name": "Health Innovations Inc",
                "Country": "Canada",
                "Start_Year": 2023,
                "Start_Month": "February"
            }
        ],
        "filter_options": {"Client_Industry": "Tech"},
        "pagination": {"page": 1, "size": 10}
    }
    response = client.post("/first_page/filter_dataframe", json=sample_data1)
    assert response.status_code == 200
    filtered_data = response.json()
    assert all(item["Client_Industry"] == "Tech" for item in filtered_data)


def test_get_descriptive_stats_endpoint():
    sample_data2 = {
        "data": [
            {
                "Result Type": "Likes",
                "Min CPM": 200.0,
                "Median CPM": 220.0,
                "Max CPM": 240.0,
                "Min CPR": 10.0,
                "Median CPR": 12.0,
                "Max CPR": 14.0,
                "Cost per Result": 1.0,
                "Cost per Mile": 0.5
            },
            {
                "Result Type": "Likes",
                "Min CPM": 300.0,
                "Median CPM": 320.0,
                "Max CPM": 340.0,
                "Min CPR": 20.0,
                "Median CPR": 22.0,
                "Max CPR": 24.0,
                "Cost per Result": 1.5,
                "Cost per Mile": 0.75
            }
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
    print("Unfiltered DataFrame Columns:")
    print(df_unfiltered.columns)  # Debugging statement to inspect columns

    print("Unfiltered DataFrame:")
    print(df_unfiltered.head())  # Debugging statement to inspect the DataFrame

    filter_input = {
        "data": df_unfiltered.to_dict(orient='records'),
        "filter_options": {"Client Industry": "Information, Tech & Telecommunications"},
        "pagination": {"page": 1, "size": 10}
    }

    response = client.post("/first_page/main", json=filter_input)
    assert response.status_code == 200
    filtered_df = response.json()
    print("Filtered DataFrame:")
    print(filtered_df)  # Debugging statement to inspect the filtered DataFrame

    assert filtered_df is not None
    assert len(filtered_df) > 0, "Filtered DataFrame is empty"


if __name__ == "__main__":
    pytest.main()
