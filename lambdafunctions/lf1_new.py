import json
import os
import boto3
import requests
import certifi
from requests_aws4auth import AWS4Auth

# OpenSearch Configuration
opensearch_host = 'https://search-photos-xpic4374vmunyumswyzwftvsyi.aos.us-east-1.on.aws'  # Replace with your OpenSearch endpoint
index_name = 'photos'
doc_type = '_doc'  # OpenSearch uses '_doc' for all document types.

# AWS Credentials
AWS_ACCESS_KEY = 'AKIAQZFG5JYFOWX7IPWN'
AWS_SECRET_KEY = 'cUYO45lmYXiV9CznJiVLvM5HvJaVv165xYs2Q5kq'
REGION = 'us-east-1'  

# AWS SigV4 Authentication
awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')

# Initialize AWS Clients
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

rekognition_client = boto3.client(
    'rekognition',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

# OpenSearch Index Mapping
mapping = {
    "mappings": {
        "properties": {
            "objectKey": {"type": "keyword"},
            "bucket": {"type": "keyword"},
            "createdTimestamp": {"type": "date"},
            "labels": {"type": "text"}
        }
    }
}

# Create the Index in OpenSearch
def create_index():
    """
    Create the photos index in OpenSearch
    """
    url = f"{opensearch_host}/{index_name}"
    headers = {"Content-Type": "application/json"}
    
    response = requests.put(url, auth=awsauth, headers=headers, data=json.dumps(mapping))
    if response.status_code not in [200, 201]:
        print(f"Failed to create index: {response.text}")
    else:
        print("Index created successfully.")

# Detect Labels using Rekognition
def detect_image_labels(bucket, key):
    """
    Use Rekognition to detect labels in the image
    
    :param bucket: S3 bucket name
    :param key: S3 object key
    :return: List of detected labels
    """
    try:
        response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=10,
            MinConfidence=70
        )
        labels = [label['Name'].lower() for label in response['Labels']]
        return labels
    except Exception as e:
        print(f"Error detecting labels: {e}")
        return []

# Get Custom Labels from S3 Metadata
def get_custom_labels(bucket, key):
    """
    Retrieve custom labels from S3 object metadata
    
    :param bucket: S3 bucket name
    :param key: S3 object key
    :return: List of custom labels
    """
    try:
        head_response = s3_client.head_object(Bucket=bucket, Key=key)
        custom_labels_str = head_response.get('Metadata', {}).get('customlabels', '')
        return [label.strip().lower() for label in custom_labels_str.split(',') if label.strip()]
    except Exception as e:
        print(f"Error retrieving custom labels: {e}")
        return []

# Prepare Photos Data for OpenSearch
def prepare_photos_opensearch_data(bucket, key):
    """
    Prepare photo data for OpenSearch indexing
    
    :param bucket: S3 bucket name
    :param key: S3 object key
    :return: Prepared document
    """
    try:
        head_response = s3_client.head_object(Bucket=bucket, Key=key)
        created_timestamp = head_response.get('LastModified').isoformat()
        rekognition_labels = detect_image_labels(bucket, key)
        custom_labels = get_custom_labels(bucket, key)
        all_labels = list(set(rekognition_labels + custom_labels))
        return {
            'objectKey': key,
            'bucket': bucket,
            'createdTimestamp': created_timestamp,
            'labels': all_labels
        }
    except Exception as e:
        print(f"Error preparing photo data: {e}")
        return None

# Index Data into OpenSearch
def index_photos_to_opensearch(documents):
    """
    Index photos data to OpenSearch
    """
    headers = {"Content-Type": "application/json"}
    for doc in documents:
        url = f"{opensearch_host}/{index_name}/{doc_type}/"
        response = requests.post(url, auth=awsauth, headers=headers, data=json.dumps(doc))
        if response.status_code not in [200, 201]:
            print(f"Failed to index document: {response.text}")
        else:
            print(f"Successfully indexed document: {doc['objectKey']}")

def lambda_handler(event, context):
    """
    Lambda function handler for S3 PUT events
    
    :param event: S3 event triggering the Lambda
    :param context: Lambda context object
    """
    try:
        # Extract S3 event details
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            if key.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                document = prepare_photos_opensearch_data(bucket, key)
                if document:
                    index_photos_to_opensearch([document])
            # Validate file type (optional - add more image extensions if needed)
            else:
                print(f"Skipping non-image file: {key}")
                continue
            
            # Index the photo
            
        return {
            'statusCode': 200,
            'body': json.dumps('Photo indexing completed successfully')
        }
    
    except Exception as e:
        print(f"Error processing event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
# Main Execution
if __name__ == "__main__":
    
    
    # Example photo
    bucket = "b2-buckett"
    key = "test-photo.jpg"

    # Validate file type
    if key.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        document = prepare_photos_opensearch_data(bucket, key)
        print(document)
        # if document:
        #     index_photos_to_opensearch([document])
