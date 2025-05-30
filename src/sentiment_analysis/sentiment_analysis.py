import json
import boto3
import pandas as pd
from io import StringIO
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Perform sentiment analysis on movie plots using VADER
    """
    try:
        bucket = event['bucket']
        input_key = event['input_key']
        output_key = event.get('output_key', 'output/movie_sentiment_results.csv')
        
        # Initialize VADER sentiment analyzer
        analyzer = SentimentIntensityAnalyzer()
        
        # Read the preprocessed dataset from S3
        response = s3.get_object(Bucket=bucket, Key=input_key)
        csv_str = response['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_str))
        
        # Check required columns
        if 'plot_cleaned' not in df.columns:
            return {
                "status": "error",
                "message": "plot_cleaned column not found. Run preprocessing first."
            }
        
        # Perform sentiment analysis
        sentiment_results = []
        
        for _, row in df.iterrows():
            plot_text = row['plot_cleaned']
            
            # Get VADER sentiment scores
            scores = analyzer.polarity_scores(plot_text)
            
            # Determine overall sentiment
            if scores['compound'] >= 0.05:
                sentiment = 'positive'
            elif scores['compound'] <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            sentiment_results.append({
                'compound_score': scores['compound'],
                'positive_score': scores['pos'],
                'neutral_score': scores['neu'],
                'negative_score': scores['neg'],
                'sentiment_label': sentiment
            })
        
        # Add sentiment results to dataframe
        sentiment_df = pd.DataFrame(sentiment_results)
        result_df = pd.concat([df, sentiment_df], axis=1)
        
        # Save results to S3
        csv_buffer = StringIO()
        result_df.to_csv(csv_buffer, index=False)
        
        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        # Calculate summary statistics
        sentiment_counts = result_df['sentiment_label'].value_counts().to_dict()
        avg_compound_score = float(result_df['compound_score'].mean())
        
        return {
            "status": "success",
            "message": "Sentiment analysis completed",
            "results": {
                "total_movies_analyzed": len(result_df),
                "sentiment_distribution": sentiment_counts,
                "average_compound_score": round(avg_compound_score, 3),
                "output_location": f"s3://{bucket}/{output_key}"
            },
            "output_key": output_key
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in sentiment analysis: {str(e)}"
        }