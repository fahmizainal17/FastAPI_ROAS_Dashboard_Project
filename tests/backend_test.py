import pytest
import pandas as pd
from unittest.mock import patch
from tests.routers.test_autoforecaster_module import filter_dataframe, get_descriptive_stats, load_campaigns_df_mock, FilterInput, importDataS3, get_s3_config

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
    df_unfiltered = load_campaigns_df_mock()
    filter_input = FilterInput(data=df_unfiltered.to_dict(orient='records'), filter_options={})
    filtered_df = filter_dataframe(pd.DataFrame(filter_input.data), filter_input.filter_options)
    assert filtered_df is not None
    assert len(filtered_df) == 2

def test_load_data():
    with patch('tests.routers.test_autoforecaster_module.importDataS3.load_df') as mock_load_df:
        mock_load_df.return_value = pd.DataFrame({
            "data": ["data1", "data2"]
        }).to_dict(orient='records')

        s3_config = get_s3_config()
        s3_storage = importDataS3(s3_config['aws_access_key_id'], s3_config['aws_secret_access_key'], s3_config['bucket_name'])
        df = s3_storage.load_df("test_key")
        assert len(df) == 2
        assert df[0]["data"] == "data1"

# Running the tests directly if this file is executed
if __name__ == "__main__":
    pytest.main()
