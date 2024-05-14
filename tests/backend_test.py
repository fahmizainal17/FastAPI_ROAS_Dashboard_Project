import pytest
import pandas as pd
from tests.routers.test_autoforecaster_module import filter_dataframe, get_descriptive_stats

@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
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
    """Provide filter options for testing."""
    return {
        'Client Industry': 'Tech',
        'Country': 'USA'
    }

def test_filter_dataframe(sample_data, filter_options):
    """Test the filter_dataframe function."""
    result = filter_dataframe(sample_data, filter_options)
    # Assert all results match the filter criteria
    assert all(result['Client Industry'] == 'Tech')
    assert all(result['Country'] == 'USA')
    assert not result.empty

def test_get_descriptive_stats(sample_data):
    """Test the get_descriptive_stats function."""
    # Adjust this test depending on what get_descriptive_stats actually returns
    result = get_descriptive_stats(sample_data)
    # Check for expected structure, e.g., columns
    expected_columns = {'min_cpr', 'median_cpr', 'max_cpr', 'min_cpm', 'median_cpm', 'max_cpm'}
    assert set(result.columns).intersection(expected_columns) == expected_columns
    assert not result.empty

# Running the tests directly if this file is executed
if __name__ == "__main__":
    pytest.main()
