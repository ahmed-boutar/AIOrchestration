import boto3
import os
from dotenv import load_dotenv

load_dotenv()

aws_region = os.getenv("AWS_REGION")
bucket_name = os.getenv("S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=aws_region,
)

def upload_file_to_s3(local_path, s3_key):
    try:
        s3.upload_file(
            Filename=local_path,
            Bucket=bucket_name,
            Key=s3_key,
        )
        print(f"Uploaded '{local_path}' to 's3://{bucket_name}/{s3_key}'")
    except Exception as e:
        print("Upload failed:", e)


def main():
    upload_file_to_s3("data/movie_sentiment_dataset.csv", os.getenv("S3_DATASET_KEY"))

if __name__ == "__main__":
    main()

