from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError
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

router = APIRouter()

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

    fb_page_name = df.loc[~df['Facebook Page Name'].isnull(), 'Facebook Page Name'].unique()
    client_industry = df.loc[~df['Client Industry'].isnull(), 'Client Industry'].unique()
    fb_page_category = df.loc[~df['Facebook Page Category'].isnull(), 'Facebook Page Category'].unique()
    objective = df.loc[~df['Ads Objective'].isnull(), 'Ads Objective'].unique()
    start_year = df.loc[~df['Start Year'].isnull(), 'Start Year'].unique()
    res_type = df.loc[~df['Result Type'].isnull(), 'Result Type'].unique()
    country_id = df.loc[~df['Country'].isnull(), 'Country'].unique()

    filter_options.sort()
    client_industry.sort()
    fb_page_category.sort()
    fb_page_name.sort()
    objective.sort()
    start_year.sort()
    res_type.sort()
    country_id.sort()

    available_client_list = pd.DataFrame(df['Facebook Page Name'].unique(), columns=['Available clients'])
    available_client_list.dropna(inplace=True)
    available_client_list = available_client_list['Available clients'].sort_values(ascending=True)

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
# Utility Functions and Classes
#################################################

def get_storage_config():
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    return {
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
        "bucket_name": bucket_name
    }
 
class importDataS3:
    def __init__(self, aws_access_key_id, aws_secret_access_key, bucket_name):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.bucket_name = bucket_name

    def load_df(self, key):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            df = pd.read_csv(response['Body'], na_filter=True, on_bad_lines='skip')
        except:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            df = pd.read_parquet(response['Body'])
        
        return df

#################################################
# Campaigns Dataset Loader Endpoint
#################################################

@st.cache_data(ttl=86400)
def load_campaigns_df() -> pd.DataFrame:
    storage_config = get_storage_config()
    s3_dl = importDataS3(storage_config['aws_access_key_id'], 
                         storage_config['aws_secret_access_key'], 
                         storage_config['bucket_name'])

    df = s3_dl.load_df('campaign_final.csv')
    
    df['Campaign ID'] = df['Campaign ID'].astype('string')
    df['Result Type'] = df['Result Type'].str.replace('_', ' ').str.title()
    df['Ads Objective'] = df['Ads Objective'].str.replace('_', ' ').str.title()
    df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d')
    df['Stop Date'] = pd.to_datetime(df['Stop Date'], format='%Y-%m-%d')

    return df.sort_values(['Start Date'], ascending=False)

def load_campaigns_df_mock() -> pd.DataFrame:
    data = {
        "Campaign ID": ["1", "2"],
        "Client Industry": ["Tech", "Health"],
        "Facebook Page Name": ["TechPage", "HealthPage"],
        "Facebook Page Category": ["Business", "Medical"],
        "Ads Objective": ["Awareness", "Engagement"],
        "Start Year": [2020, 2021],
        "Result Type": ["Likes", "Comments"],
        "Country": ["USA", "Canada"]
    }
    return pd.DataFrame(data)

#################################################
# Load Data from AWS S3 Endpoint
#################################################

class LoadDataInput(BaseModel):
    key: str

@router.get("/load-data/{key}")
def load_data(key: str):
    storage_config = get_storage_config()
    if not storage_config["aws_access_key_id"] or not storage_config["aws_secret_access_key"]:
        raise HTTPException(status_code=500, detail="Storage configuration is missing.")
    
    s3_storage = importDataS3(storage_config['aws_access_key_id'], storage_config['aws_secret_access_key'], storage_config['bucket_name'])
    df = s3_storage.load_df(key)
    return df.to_dict(orient='records')

#################################################
# Main Endpoint
#################################################

@router.post("/main")
def main():
    df_unfiltered = load_campaigns_df()
    filter_input = FilterInput(data=df_unfiltered.to_dict(orient='records'), filter_options={})
    filtered_df = filter_dataframe(pd.DataFrame(filter_input.data), filter_input.filter_options)
    return filtered_df.to_dict(orient='records')

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
