import os
import re
import pandas as pd
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

def get_storage_config():
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "bucket_name": os.getenv("S3_BUCKET_NAME")
    }

class ImportDataS3:
    """Class to load data from AWS S3"""
    def __init__(self, aws_access_key_id, aws_secret_access_key, bucket_name):
        if not aws_access_key_id or not aws_secret_access_key:
            raise NoCredentialsError()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = bucket_name

    def load_df(self, key):
        """Loads data in either .CSV or .parquet format."""
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            if key.endswith('.csv'):
                return pd.read_csv(BytesIO(obj['Body'].read()))
            elif key.endswith('.parquet'):
                return pd.read_parquet(BytesIO(obj['Body'].read()))
            else:
                raise ValueError("Unsupported file type.")
        except NoCredentialsError:
            raise
        except Exception as e:
            raise Exception(f"Failed to load data from S3: {str(e)}") from e

# Load AWS credentials from environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("S3_BUCKET_NAME")

# Initialize the ImportDataS3 instance
decoris_dl = ImportDataS3(aws_access_key_id, aws_secret_access_key, bucket_name)

def load_clients_df() -> pd.DataFrame:
    """Loads the clients dataframe."""
    return decoris_dl.load_df('clients_data_final.parquet')

def load_roas_df() -> pd.DataFrame:
    """Loads the ROAS dataframe."""
    df = decoris_dl.load_df('roas_final.csv')
    df['Campaign ID'] = df['Campaign ID'].astype('string')
    df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d')
    df['Stop Date'] = pd.to_datetime(df['Stop Date'], format='%Y-%m-%d')
    return df.sort_values(['Start Date'], ascending=False)


def load_campaigns_df() -> pd.DataFrame:
    """Loads the Campaigns dataframe."""
    df = decoris_dl.load_df('campaign_final.parquet')
    df['Campaign ID'] = df['Campaign ID'].astype('string')
    df['Result Type'] = df['Result Type'].str.replace('_', ' ').str.title()
    df['Ads Objective'] = df['Ads Objective'].str.replace('_', ' ').str.title()
    
    # Convert dates with error handling
    df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d', errors='coerce', dayfirst=True)
    df['Stop Date'] = pd.to_datetime(df['Stop Date'], format='%Y-%m-%d', errors='coerce', dayfirst=True)

    # Fill NaT with default dates
    df['Start Date'] = df['Start Date'].fillna('2019-01-01')
    df['Stop Date'] = df['Stop Date'].fillna(datetime.today().strftime('%Y-%m-%d'))
    
    # Ensure dates are in a format that is JSON serializable
    df['Start Date'] = df['Start Date'].dt.strftime('%Y-%m-%d')
    df['Stop Date'] = df['Stop Date'].dt.strftime('%Y-%m-%d')

    # Convert 'Cost per Result' and 'Cost per Mile' to numeric
    df['Cost per Result'] = pd.to_numeric(df['Cost per Result'], errors='coerce')
    df['Cost per Mile'] = pd.to_numeric(df['Cost per Mile'], errors='coerce')

    # Add missing column if necessary
    if 'Median CPR' not in df.columns:
        df['Median CPR'] = 0  # or some default value

    return df.sort_values(['Start Date'], ascending=False)



def load_adsets_df() -> pd.DataFrame:
    """Loads the Adsets dataframe."""
    df = decoris_dl.load_df('adsets_final.parquet')
    df['Result Type'] = df['Result Type'].str.replace('_', ' ').str.title()
    df[['Adset ID', 'Campaign ID']] = df[['Adset ID', 'Campaign ID']].astype('string')

    pattern = r'(\b[A-Z]+\b):[ \t]+(.*?)(?=[A-Z]+:|$)'

    def format_text(text):
        matches = re.findall(pattern, text, re.MULTILINE)
        formatted_data = {label: items.split(",") for label, items in matches}

        temp = []
        for label, items in formatted_data.items():
            temp.append(f"{label}:\n{', '.join(map(str.strip, items))}")

        final_data = "\n".join(temp)
        return final_data

    df['Psychographic'] = df['Psychographic'].str.replace('"', " ").str.replace(":,", ": ").apply(format_text)

    return df[[
        'Client Industry',
        'Facebook Page Name',
        'Facebook Page Category',
        'Adset Name',
        'Result Type',
        'Total Results',
        'Age Range',
        'Gender',
        'Country',
        'Psychographic',
        'Custom Audiences',
        'Campaign Name',
        'Campaign ID',
        'Adset ID',
        'Start Date',
        'End Date'
    ]]

def convert_df(df: pd.DataFrame):
    """Converts a pandas dataframe to CSV for download."""
    return df.to_csv().encode('utf-8')

def load_feedback_form(sheets_url: str) -> pd.DataFrame:
    """Loads feedback form data from a public Google Sheet."""
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)
