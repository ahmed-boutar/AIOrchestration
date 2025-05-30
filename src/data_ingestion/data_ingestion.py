import json
import boto3
import pandas as pd
from io import StringIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Load movie sentiment dataset from S3 and return basic info
    Expected event: {"bucket": "ml-orchestration-bucket", "input_key": "data/movie_sentiment_analysis.csv"}
    """
    try:
        bucket = event['bucket']
        input_key = event['input_key']
        
        # Read the dataset from S3
        response = s3.get_object(Bucket=bucket, Key=input_key)
        csv_str = response['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_str))
        
        # Basic validation
        required_columns = ['title', 'year', 'plot']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "status": "error",
                "message": f"Missing required columns: {missing_columns}",
                "available_columns": list(df.columns)
            }
        
        # Basic dataset info
        dataset_info = {
            "total_rows": len(df),
            "columns": list(df.columns),
            "sample_titles": df['title'].head(3).tolist(),
            "year_range": f"{df['year'].min()}-{df['year'].max()}" if 'year' in df.columns else "N/A",
            "null_plots": df['plot'].isnull().sum()
        }
        
        return {
            "status": "success",
            "message": "Dataset loaded successfully",
            "dataset_info": dataset_info,
            "next_step": "preprocess_data"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading dataset: {str(e)}"
        }