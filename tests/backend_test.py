import os
import pytest
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from tests.routers.test_autoforecaster_module import filter_dataframe, get_descriptive_stats, FilterInput, get_storage_config, load_campaigns_df, get_forecast_by_value
from tests.routers.load_exp_data_utils import ImportDataS3, load_clients_df, load_roas_df, load_campaigns_df, load_adsets_df, convert_df, load_feedback_form 
from tests.routers.miscellaneous_utils import round_to_two_decimal_places_with_min 

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def sample_data():
    data = {
        'Client Industry': ['Tech', 'Health', 'Tech', 'Education'],
        'Facebook Page Name': ['TechPage', 'HealthPage', 'TechPage', 'EduPage'],
        'Facebook Page Category': ['Business', 'Medical', 'Business', 'Education'],
        'Ads Objective': ['Awareness', 'Conversion', 'Awareness', 'Engagement'],
        'Start Year': [2020, 2021, 2020, 2022],
        'Result Type': ['Likes', 'Sales', 'Likes', 'Comments'],
        'Country': ['USA', 'Canada', 'USA', 'UK']
    }
    return pd.DataFrame(data)

@pytest.fixture
def filter_options():
    return {
        'Client Industry': 'Tech',
        'Country': 'USA'
    }

def test_filter_dataframe(sample_data, filter_options):
    result = filter_dataframe(sample_data, filter_options)
    assert all(result['Client Industry'] == 'Tech')
    assert all(result['Country'] == 'USA')
    assert not result.empty

@pytest.fixture
def sample_data_descriptive():
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

def test_get_descriptive_stats(sample_data_descriptive):
    result = get_descriptive_stats(sample_data_descriptive)
    expected_columns = {'Min CPR', 'Median CPR', 'Max CPR', 'Min CPM', 'Median CPM', 'Max CPM'}
    assert set(result.columns).intersection(expected_columns) == expected_columns
    assert not result.empty

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

def test_get_forecast_by_value2(sample_data_descriptive2):
    budget = 1000
    
    distribution = {
        'Likes': 40,
        'Sales': 30,
        'Comments': 30
    }

    result = get_forecast_by_value(sample_data_descriptive2, budget, distribution)
    
    # Check that the result is not empty
    assert not result.empty

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
    assert all(column in result.columns for column in expected_columns)

def test_load_data_from_s3():
    storage_config = get_storage_config()
    print("AWS_ACCESS_KEY_ID:", storage_config['aws_access_key_id'])  # Debugging statement
    print("AWS_SECRET_ACCESS_KEY:", storage_config['aws_secret_access_key'])  # Debugging statement
    print("BUCKET_NAME:", storage_config['bucket_name'])  # Debugging statement

    assert storage_config['aws_access_key_id'] is not None, "AWS_ACCESS_KEY_ID is not set in .env"
    assert storage_config['aws_secret_access_key'] is not None, "AWS_SECRET_ACCESS_KEY is not set in .env"
    assert storage_config['bucket_name'] is not None, "BUCKET_NAME is not set in .env"

    s3_storage = ImportDataS3(storage_config['aws_access_key_id'], 
                              storage_config['aws_secret_access_key'], 
                              storage_config['bucket_name'])
    df = s3_storage.load_df(os.getenv("OBJECT_NAME_1"))
    assert not df.empty, "DataFrame loaded from S3 is empty"
    assert 'Campaign ID' in df.columns, "Expected column 'Campaign ID' not found in DataFrame"
    assert 'Result Type' in df.columns, "Expected column 'Result Type' not found in DataFrame"

def test_main():
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

    filtered_df = filter_dataframe(pd.DataFrame(filter_input["data"]), filter_input["filter_options"])
    print("Filtered DataFrame Columns:")
    print(filtered_df.columns)  # Debugging statement to inspect columns

    print("Filtered DataFrame:")
    print(filtered_df.head())  # Debugging statement to inspect the filtered DataFrame

    assert filtered_df is not None
    assert len(filtered_df) > 0, "Filtered DataFrame is empty"

    try:
        stats_df = get_descriptive_stats(filtered_df)
        print("Descriptive Statistics DataFrame:")
        print(stats_df.head())  # Debugging statement to inspect the stats DataFrame
    except ValueError as e:
        print(e)
        raise

# Running the tests directly if this file is executed
if __name__ == "__main__":
    pytest.main()
