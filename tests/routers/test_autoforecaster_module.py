from fastapi import HTTPException, APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError
from pydantic import BaseModel
import os
import logging
from io import BytesIO
from typing import List, Dict, Any
import numpy as np
from tests.routers.load_exp_data_utils import ImportDataS3, load_clients_df, load_roas_df, load_campaigns_df, load_adsets_df, convert_df, load_feedback_form, get_storage_config
from tests.routers.miscellaneous_utils import round_to_two_decimal_places_with_min 

#################################################
# Utility Functions and Classes
#################################################

load_dotenv() 

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

#################################################
# Filter Dataframe Endpoint
#################################################

class FilterInput(BaseModel):
    data: list
    filter_options: dict

@router.post("/filter_dataframe", response_model=list)
def filter_dataframe_endpoint(input: FilterInput):
    df = pd.DataFrame(input.data)
    filtered_df = filter_dataframe(df, input.filter_options)
    return filtered_df.to_dict(orient='records')

def filter_dataframe(df: pd.DataFrame, options: dict) -> pd.DataFrame:
    df = df.copy()
    
    for key, value in options.items():
        if key in df.columns:
            if isinstance(value, list):
                df = df[df[key].isin(value)]
            else:
                df = df[df[key] == value]
    return df

#################################################
# Get Descriptive Stats Endpoint
#################################################

class StatsInput(BaseModel):
    data: List[Dict[str, Any]]

@router.post("/get_descriptive_stats", response_model=List[Dict[str, Any]])
def get_descriptive_stats_endpoint(input: StatsInput):
    df = pd.DataFrame(input.data)
    return get_descriptive_stats(df).to_dict(orient='records')

def get_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    best_campaign_sets = []
    for result_types in df['Result Type'].unique():
        median_cpr = df.loc[df['Result Type'] == result_types, 'Median CPR'].median(skipna=True)
        median_cpm = df.loc[df['Result Type'] == result_types, 'Median CPM'].median(skipna=True)

        min_cpr = df.loc[df['Result Type'] == result_types, 'Min CPR'].quantile(q=0.25, interpolation='midpoint')
        min_cpm = df.loc[df['Result Type'] == result_types, 'Min CPM'].quantile(q=0.25, interpolation='midpoint')

        max_cpr = df.loc[df['Result Type'] == result_types, 'Max CPR'].quantile(q=0.80, interpolation='midpoint')
        max_cpm = df.loc[df['Result Type'] == result_types, 'Max CPM'].quantile(q=0.80, interpolation='midpoint')

        num_campaigns = len(df.loc[df['Result Type'] == result_types])

        metrics = {
            'Result Type': result_types,
            'Min CPM': round_to_two_decimal_places_with_min(min_cpm),
            'Median CPM': round_to_two_decimal_places_with_min(median_cpm),
            'Max CPM': round_to_two_decimal_places_with_min(max_cpm),
            'Min CPR': round_to_two_decimal_places_with_min(min_cpr),
            'Median CPR': round_to_two_decimal_places_with_min(median_cpr),
            'Max CPR': round_to_two_decimal_places_with_min(max_cpr),
            'No. of Campaigns': num_campaigns,
        }

        df_metrics_by_industry = pd.DataFrame(metrics, index=[0])
        best_campaign_sets.append(df_metrics_by_industry)

    df_best_roas_sets = pd.concat(best_campaign_sets)
    return df_best_roas_sets

#################################################
# Get Forecast By Value Endpoint
#################################################

class ForecastInput(BaseModel):
    data: List[Dict[str, Any]]
    budget: float
    distribution: Dict[str, int]

@router.post("/get_forecast_by_value", response_model=List[Dict[str, Any]])
def get_forecast_by_value_endpoint(input: ForecastInput):
    df = pd.DataFrame(input.data)
    return get_forecast_by_value(df, input.budget, input.distribution).to_dict(orient='records')

def get_forecast_by_value(df: pd.DataFrame, budget: float, distribution: dict[str, int]) -> pd.DataFrame:
    """
    Function that uses the output dataframe from `get_descriptive_stats()`
    to calculate projections of campaign results for Impressions and Results e.g.,
    purchases, messages, likes, etc.

    ### Arguments
    - `df`: the output pandas dataframe from `get_descriptive_stats()`
    - `budget`: the total budget allocated for the campaign
    - `distribution`: a dictionary where keys are result types and values are the distribution percentages

    ### Return
    A dataframe with the following metrics:
    - `Ad Spent`: The amount spent on the campaign
    - `Max Impressions`: The number of times the ad is shown
    - `Median Impressions`
    - `Min Impressions`
    - `Max Results`: The best results (e.g., num. of likes, purchases, etc.)
    from a particular campaign
    - `Median Results`
    - `Min Results`
    """

    df = df.copy()

    # Filter the distribution to include only result types present in the DataFrame
    filtered_distribution = {k: v for k, v in distribution.items() if k in df['Result Type'].values}
    
    # Adjust the percentages to add up to 100%
    total_percentage = sum(filtered_distribution.values())
    if total_percentage != 100:
        factor = 100 / total_percentage
        filtered_distribution = {k: v * factor for k, v in filtered_distribution.items()}

    result_dict = {
        'Result Type': [],
        'Distribution (%)': []
    }

    for result_type, percentage in filtered_distribution.items():
        result_dict['Result Type'].append(result_type)
        result_dict['Distribution (%)'].append(percentage)

    # Create a DataFrame from the result dictionary
    df_money = pd.DataFrame(result_dict)
    df_money['Ad Spent'] = (df_money['Distribution (%)'] / 100) * budget

    # Ensure the total Ad Spent sums to the budget
    total_spent = df_money['Ad Spent'].sum()
    if total_spent != budget:

        df_money['Ad Spent'] = df_money['Ad Spent'] * (budget / total_spent)

    df_final = pd.merge(df, df_money, on='Result Type')

    df_final['Max Impressions'] = round((df_final['Ad Spent'] / df_final['Min CPM']) * 1000)
    df_final['Median Impressions'] = round((df_final['Ad Spent'] / df_final['Median CPM']) * 1000)
    df_final['Min Impressions'] = round((df_final['Ad Spent'] / df_final['Max CPM']) * 1000)

    df_final['Max Results'] = round(df_final['Ad Spent'] / df_final['Min CPR'])
    df_final['Median Results'] = round(df_final['Ad Spent'] / df_final['Median CPR'])
    df_final['Min Results'] = round(df_final['Ad Spent'] / df_final['Max CPR'])

    df_final = df_final[[
        'Result Type',
        'Ad Spent',
        'Max Impressions',
        'Median Impressions',
        'Min Impressions',
        'Max Results',
        'Median Results',
        'Min Results',
    ]]

    return df_final

# #################################################
# # Load Data from AWS S3 Endpoint 
# #################################################
# # Its Backend Function is ImportDataS3 & get_storage_config
# class LoadDataInput(BaseModel):
#     key: str

# @router.get("/load-data/{key}")
# async def load_data(key: str):
#     storage_config = get_storage_config()
#     if not storage_config['aws_access_key_id'] or not storage_config['aws_secret_access_key']:
#         raise HTTPException(status_code=500, detail="Storage configuration is missing.")
    
#     s3_storage = ImportDataS3(storage_config['aws_access_key_id'], storage_config['aws_secret_access_key'], storage_config['bucket_name'])
#     df = s3_storage.load_df(key)
    
#     buffer = BytesIO()
#     df.to_parquet(buffer, index=False)
#     buffer.seek(0)
    
#     headers = {
#         'Content-Disposition': f'attachment; filename="{key}"',
#         'Content-Type': 'application/octet-stream'
#     }
    
#     return StreamingResponse(buffer, headers=headers, media_type="application/octet-stream")


#################################################
# Main Endpoint
#################################################

@router.post("/main", response_model=list)
def main():
    df_unfiltered = load_campaigns_df()
    filter_input = FilterInput(data=df_unfiltered.to_dict(orient='records'), filter_options={})
    filtered_df = filter_dataframe(pd.DataFrame(filter_input.data), filter_input.filter_options)
    return filtered_df.to_dict(orient='records')

