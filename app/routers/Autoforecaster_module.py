from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import boto3
from botocore.client import Config
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import os

load_dotenv()
app = FastAPI(
      title="Streamlit ROAS Dashboard API",
      summary="A collection of endpoints for FastAPI ROAS Dashboard",
      version="0.1.0",
      docs_url="/docs",
      openapi_url="/openapi.json",
)

#################################################
# Welcome Page Endpoint
#################################################

@app.get("/", response_class=HTMLResponse, summary="Welcome_Page", tags=["Root_Of_FastAPI_Application"])
def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to FastAPI For ROAS Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                text-align: center;
            }
            h1 {
                color: #333;
            }
            p {
                color: #666;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to FastAPI For ROAS Dashboard!</h1>
            <p>Thank you for visiting. This is the root of the application.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

#################################################
# Filter Dataframe Endpoint
#################################################

class FilterInput(BaseModel):
    data: list
    filter_options: dict

@app.post("/filter_dataframe", response_model=list)
def filter_dataframe(input: FilterInput):
    df = pd.DataFrame(input.data)
    return filter_dataframe_func(df, input.filter_options).to_dict(orient='records')

def filter_dataframe_func(df: pd.DataFrame, filter_options: dict) -> pd.DataFrame:
    """
    Lets the user narrow down their forecast by Client Industry,
    Facebook Page Category, Facebook Page Name, Ads Objective,
    Start Year, Result Type and Country.

    ### Args:
    - `df`: An unfiltered pandas dataframe.
    - `filter_options`: A dictionary with filter options.

    ### Return:
    A filtered pandas dataframe
    """
    df = df.copy()

    filter_fields = [
        'Client Industry',
        'Facebook Page Name',
        'Facebook Page Category',
        'Ads Objective', 'Start Year',
        'Result Type', 'Country'
    ]

    for field in filter_fields:
        if field in filter_options and filter_options[field]:
            df = df[df[field].isin(filter_options[field])]

    return df

#################################################
# Get Descriptive Stats Endpoint
#################################################

class StatsInput(BaseModel):
    data: list

@app.post("/get_descriptive_stats", response_model=list)
def get_descriptive_stats(input: StatsInput):
    df = pd.DataFrame(input.data)
    return get_descriptive_stats_func(df).to_dict(orient='records')

def round_to_two_decimal_places_with_min(value: float):
    """
    This function is used to round decimal values
    up to 2 decimal places. However, there are instances
    where rounding to two decimal places still yields 0.00.
    This poses problems when forecasting results. Hence, 
    we'll set the minimum this function can possibly return to
    be 0.01

    ### Args:
    - `value`: A float

    ### Returns:
    A float rounded to 2 decimal places or 0.01 if
    the rounded value is smaller than 0.01.
    """
    rounded_value = round(value, 2)
    return max(rounded_value, 0.01)

def get_descriptive_stats_func(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function to get descriptive stats from the filtered dataframe, which
    will be used to generate projections on campaign performance. We'd
    ideally use a machine learning approach, but can't due to data limitations.
    Hence, we'll instead use the IQR (Inter-quartile range) to make
    these estimates. 

    ### Args
    - `df`: A pandas dataframe

    ### Return
    A pandas dataframe with the following fields as columns:
    - `min_cpr`: Minimum Cost per Result e.g., purchases, messages,
    likes, etc.
    - `median_cpr`
    - `max_cpr`
    - `min_cpm`: Minimum Cost per Mile
    - `median_cpm`
    - `max_cpm`
    """
    df = df.copy()
    
    best_campaign_sets = []
    for result_types in df['Result Type'].unique():
        
        # median
        median_cpr= df.loc[df['Result Type'] == result_types, 'Cost per Result'] \
                    .median(skipna=True)
        
        median_cpm= df.loc[df['Result Type'] == result_types, 'Cost per Mile'] \
                    .median(skipna=True)

        # min
        min_cpr= df.loc[df['Result Type'] == result_types, 'Cost per Result'] \
                    .quantile(q=0.25, interpolation='midpoint')
        
        min_cpm= df.loc[df['Result Type'] == result_types, 'Cost per Mile'] \
                    .quantile(q=0.25, interpolation='midpoint')

        # max
        max_cpr= df.loc[df['Result Type'] == result_types, 'Cost per Result'] \
                    .quantile(q=0.80, interpolation='midpoint')
        
        max_cpm= df.loc[df['Result Type'] == result_types, 'Cost per Mile'] \
                    .quantile(q=0.80, interpolation='midpoint')

        
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
# Load Data from AWS S3 Endpoint
#################################################

class LoadDataInput(BaseModel):
    key: str

@app.get("/load-data/{key}")
def load_data(input: LoadDataInput):
    s3_config = get_s3_config()
    if not s3_config["aws_access_key_id"] or not s3_config["aws_secret_access_key"]:
        raise HTTPException(status_code=500, detail="S3 configuration is missing.")
    s3_storage = importDataS3(s3_config['aws_access_key_id'], s3_config['aws_secret_access_key'], s3_config['bucket_name'])
    df = s3_storage.load_df(input.key)
    return df.to_dict(orient='records')

#################################################
# Utility Functions and Classes
#################################################

def get_s3_config():
    """Function to get S3 configuration securely."""
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = 'your-bucket-name'

    return {
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
        "bucket_name": bucket_name
    }

class importDataS3:
    """Class to load data from AWS S3"""
    def __init__(self, aws_access_key_id, aws_secret_access_key, bucket_name):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = bucket_name

    def load_df(self, key):
        """
        Loads data in either .CSV or .parquet format. In the future, 
        all data should be in .parquet format instead.
        """
        obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        try:
            df = pd.read_csv(obj['Body'], na_filter=True, on_bad_lines='skip')
        except:
            df = pd.read_parquet(obj['Body'])
        
        return df

#################################################
# Campaigns Dataset Loader Endpoint
#################################################

@st.cache_data(ttl=86400)
def load_campaigns_df() -> pd.DataFrame:
    """
    Loads in the Campaigns dataframe.
    
    ### Returns:
    A pandas dataframe
    """
    s3_config = get_s3_config()
    decoris_dl = importDataS3(s3_config['aws_access_key_id'], 
                              s3_config['aws_secret_access_key'], 
                              s3_config['bucket_name'])

    df = decoris_dl.load_df('campaign_final.csv')
    
    df['Campaign ID'] = df['Campaign ID'].astype('string')
    df['Result Type'] = df['Result Type'].str.replace('_', ' ').str.title()
    df['Ads Objective'] = df['Ads Objective'].str.replace('_', ' ').str.title()
    df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d')
    df['Stop Date'] = pd.to_datetime(df['Stop Date'], format='%Y-%m-%d')

    return df.sort_values(['Start Date'], ascending=False)

#################################################
# Main Endpoint
#################################################
@app.post("/main")
def main():
    df_unfiltered = load_campaigns_df()
    filter_input = FilterInput(data=df_unfiltered.to_dict(orient='records'), filter_options={})
    filtered_df = filter_dataframe_func(filter_input)
    return filtered_df


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
