import json
import boto3
import pandas as pd
import re
from io import StringIO

s3 = boto3.client('s3')

def clean_text(text):
    """
    Minimal text preprocessing for sentiment analysis
    """
    if pd.isna(text):
        return ""
    
    # Convert to string and lowercase
    text = str(text).lower()
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    
    text = re.sub(r'\[.*?\]', '', text)  # Remove brackets
    text = re.sub(r'\(.*?\)', '', text)  # Remove parentheses
    
    # Remove excessive punctuation but keep sentence structure
    text = re.sub(r'[^\w\s\.\!\?]', ' ', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text.strip()

def lambda_handler(event, context):
    """
    Preprocess movie plot data for sentiment analysis
    """
    try:
        bucket = event['bucket']
        input_key = event['input_key']
        output_key = event.get('output_key', 'preprocessed/movie_sentiment_preprocessed.csv')
        
        # Read the dataset from S3
        response = s3.get_object(Bucket=bucket, Key=input_key)
        csv_str = response['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_str))
        
        # Check required columns
        if 'plot' not in df.columns:
            return {
                "status": "error",
                "message": "Plot column not found in dataset"
            }
        
        # Create a copy for preprocessing
        df_processed = df.copy()
        
        # Clean the plot column
        df_processed['plot_cleaned'] = df_processed['plot'].apply(clean_text)
        
        # Remove rows with empty plots after cleaning
        df_processed = df_processed[df_processed['plot_cleaned'].str.len() > 0]
        
        # Add some basic stats
        df_processed['plot_length'] = df_processed['plot_cleaned'].str.len()
        df_processed['word_count'] = df_processed['plot_cleaned'].str.split().str.len()
        
        # Save preprocessed data back to S3
        csv_buffer = StringIO()
        df_processed.to_csv(csv_buffer, index=False)
        
        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        return {
            "status": "success",
            "message": "Data preprocessing completed",
            "preprocessing_stats": {
                "original_rows": len(df),
                "processed_rows": len(df_processed),
                "removed_rows": len(df) - len(df_processed),
                "avg_plot_length": int(df_processed['plot_length'].mean()),
                "avg_word_count": int(df_processed['word_count'].mean())
            },
            "output_key": output_key,
            "next_step": "sentiment_analysis"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error preprocessing data: {str(e)}"
        }