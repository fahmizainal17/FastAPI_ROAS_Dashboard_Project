from fastapi import HTTPException, APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from dotenv import load_dotenv
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError
from pydantic import BaseModel
import os
import logging
from io import BytesIO, StringIO
from typing import List, Dict, Any
import numpy as np
import aiofiles

#################################################
# Utility Functions and Classes
#################################################

load_dotenv() 

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_storage_config():
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "bucket_name": os.getenv("S3_BUCKET_NAME")
    }

router = APIRouter()

class importDataS3:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, bucket_name: str):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.bucket_name = bucket_name

    def load_df(self, key: str) -> pd.DataFrame:
        if not self.bucket_name:
            logger.error("Bucket name is not set.")
            raise ValueError("Bucket name is not set.")
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            body = response['Body'].read()
            buffer = BytesIO(body)
            df = pd.read_parquet(buffer)
            return df
        except NoCredentialsError as e:
            logger.error("AWS credentials not available.")
            raise HTTPException(status_code=500, detail="AWS credentials not available.") from e
        except Exception as e:
            logger.error(f"Failed to load data from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error loading data from S3: {str(e)}") from e


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
    
    filter_options = [
        'Client Industry',
        'Facebook Page Name',
        'Facebook Page Category',
        'Ads Objective', 'Start Year',
        'Result Type', 'Country'
    ]

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
    data: list

@router.post("/get_descriptive_stats", response_model=list)
def get_descriptive_stats_endpoint(input: StatsInput):
    df = pd.DataFrame(input.data)
    return get_descriptive_stats(df).to_dict(orient='records')

def round_to_two_decimal_places_with_min(value: float):
    rounded_value = round(value, 2)
    return max(rounded_value, 0.01)

def get_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    best_campaign_sets = []
    for result_types in df['Result Type'].unique():
        median_cpr = df.loc[df['Result Type'] == result_types, 'Cost per Result'].median(skipna=True)
        median_cpm = df.loc[df['Result Type'] == result_types, 'Cost per Mile'].median(skipna=True)

        min_cpr = df.loc[df['Result Type'] == result_types, 'Cost per Result'].quantile(q=0.25, interpolation='midpoint')
        min_cpm = df.loc[df['Result Type'] == result_types, 'Cost per Mile'].quantile(q=0.25, interpolation='midpoint')

        max_cpr = df.loc[df['Result Type'] == result_types, 'Cost per Result'].quantile(q=0.80, interpolation='midpoint')
        max_cpm = df.loc[df['Result Type'] == result_types, 'Cost per Mile'].quantile(q=0.80, interpolation='midpoint')

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
# Campaigns Dataset Loader Endpoint
#################################################

def load_campaigns_df() -> pd.DataFrame:
    storage_config = get_storage_config()
    s3_dl = importDataS3(storage_config['aws_access_key_id'], 
                         storage_config['aws_secret_access_key'], 
                         storage_config['bucket_name'])

    df = s3_dl.load_df('campaign_final.parquet')
    
    df['Campaign ID'] = df['Campaign ID'].astype('string')
    df['Result Type'] = df['Result Type'].str.replace('_', ' ').str.title()
    df['Ads Objective'] = df['Ads Objective'].str.replace('_', ' ').str.title()
    
    # Convert dates with error handling
    df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d', errors='coerce')
    df['Stop Date'] = pd.to_datetime(df['Stop Date'], format='%Y-%m-%d', errors='coerce')

    # Print rows with invalid dates for debugging
    invalid_start_dates = df[df['Start Date'].isna()]['Start Date']
    invalid_stop_dates = df[df['Stop Date'].isna()]['Stop Date']
    
    if not invalid_start_dates.empty:
        print("Invalid Start Dates:", invalid_start_dates)
    if not invalid_stop_dates.empty:
        print("Invalid Stop Dates:", invalid_stop_dates)

    return df.sort_values(['Start Date'], ascending=False)

#################################################
# Load Data from AWS S3 Endpoint
#################################################

class LoadDataInput(BaseModel):
    key: str

async def load_file(file_path: str):
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
    return content

@router.get("/first_page/load-data/{key}")
async def load_data(key: str):
    # Adjust the path to point to the root directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    file_path = os.path.join(base_dir, key)
    
    print(f"Resolved file path: {file_path}")  # Debugging statement
    
    if not os.path.exists(file_path):
        print(f"File does not exist at path: {file_path}")  # Additional debug statement
        raise HTTPException(status_code=404, detail=f"File not found at path: {file_path}")

    # Check if the file is CSV or Parquet
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        print(f"Error reading the file: {e}")  # Additional debug statement
        raise HTTPException(status_code=500, detail=f"Error reading the file: {e}")

    if df.empty:
        raise HTTPException(status_code=204, detail="No content")

    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv")

#################################################
# Main Endpoint
#################################################

@router.post("/main")
def main():
    df_unfiltered = load_campaigns_df()
    filter_input = FilterInput(data=df_unfiltered.to_dict(orient='records'), filter_options={})
    filtered_df = filter_dataframe(pd.DataFrame(filter_input.data), filter_input.filter_options)
    return filtered_df.to_dict(orient='records')