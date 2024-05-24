import os
import pytest
import pandas as pd
from dotenv import load_dotenv
from tests.routers.test_autoforecaster_module import filter_dataframe, get_descriptive_stats, FilterInput, ImportDataS3, get_storage_config, load_campaigns_df

# Load environment variables from .env file
load_dotenv()

def get_storage_config():
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "bucket_name": os.getenv("S3_BUCKET_NAME")
    }

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

def test_filter_dataframe(sample_data: pd.DataFrame, filter_options: dict[str, str]):
    result = filter_dataframe(sample_data, filter_options)
    assert all(result['Client Industry'] == 'Tech')
    assert all(result['Country'] == 'USA')
    assert not result.empty

@pytest.fixture
def sample_data_descriptive():
    data = {
        'Client Industry': ['Tech', 'Health', 'Tech', 'Education'],
        'Facebook Page Name': ['TechPage', 'HealthPage', 'TechPage', 'EduPage'],
        'Facebook Page Category': ['Business', 'Medical', 'Business', 'Education'],
        'Ads Objective': ['Awareness', 'Conversion', 'Awareness', 'Engagement'],
        'Start Year': [2020, 2021, 2020, 2022],
        'Result Type': ['Likes', 'Sales', 'Likes', 'Comments'],
        'Country': ['USA', 'Canada', 'USA', 'UK'],
        'Cost per Result': [10.0, 20.0, 15.0, 25.0],
        'Cost per Mile': [200.0, 300.0, 250.0, 350.0]
    }
    return pd.DataFrame(data)

def test_get_descriptive_stats(sample_data_descriptive: pd.DataFrame):
    result = get_descriptive_stats(sample_data_descriptive)
    expected_columns = {'Min CPR', 'Median CPR', 'Max CPR', 'Min CPM', 'Median CPM', 'Max CPM'}
    assert set(result.columns).intersection(expected_columns) == expected_columns
    assert not result.empty

def test_main():
    df_unfiltered = load_campaigns_df()
    filter_input = FilterInput(data=df_unfiltered.to_dict(orient='records'), filter_options={})
    filtered_df = filter_dataframe(pd.DataFrame(filter_input.data), filter_input.filter_options)
    assert filtered_df is not None
    assert len(filtered_df) > 0

def test_load_data_from_s3():
    storage_config = get_storage_config()
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

# Running the tests directly if this file is executed
if __name__ == "__main__":
    pytest.main()