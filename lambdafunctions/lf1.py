import json
import os
import boto3
import requests
import certifi
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch
from elastic_transport import Transport



# Extract AWS credentials from environment variables
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

AWS_ACCESS_KEY = 'AKIAQZFG5JYFOWX7IPWN'
AWS_SECRET_KEY = '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'
REGION = 'us-east-1'  

awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')

# Elasticsearch configuration
HOST = 'search-photos-xpic4374vmunyumswyzwftvsyi.aos.us-east-1.on.aws'  # Replace with your OpenSearch endpoint
INDEX = 'photos'

# Initialize AWS clients
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='us-east-1'  
)

rekognition_client = boto3.client(
    'rekognition',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='us-east-1'  
)





def connect_elasticsearch():
    """
    Establish connection to Elasticsearch
    """
    
    
    awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')
    try:
        # Create the AWS authentication object
        awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')
        
        # Configure the Elasticsearch client
        es = Elasticsearch(
            hosts=[f'https://{HOST}'],
            http_auth=awsauth,
            verify_certs=True,
            ca_certs=certifi.where(),
            request_timeout=30,  # Updated from timeout to request_timeout
            node_class="requests",
            retry_on_timeout=True,
            max_retries=3
        )
        
        # Test the connection with more detailed error reporting
        try:
            if not es.ping():
                raise Exception("Ping failed")
            # Try to get cluster info as an additional connection test
            info = es.info()
            print(f"Successfully connected to Elasticsearch cluster: {info.get('cluster_name', 'unknown')}")
            return es
        except Exception as ping_error:
            print(f"Connection test failed: {str(ping_error)}")
            # Try to get more detailed error information
            try:
                health = es.cluster.health()
                print(f"Cluster health: {health}")
            except Exception as health_error:
                print(f"Could not get cluster health: {str(health_error)}")
            raise
            
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return None


def detect_image_labels(bucket, key):
    """
    Use Rekognition to detect labels in the image
    
    :param bucket: S3 bucket name
    :param key: S3 object key
    :return: List of detected labels
    """
    try:
        # Detect labels using Rekognition
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10,  # Adjust as needed
            MinConfidence=70  # Confidence threshold
        )
        
        # Extract label names
        labels = [label['Name'].lower() for label in response['Labels']]
        return labels
    except Exception as e:
        print(f"Error detecting labels: {e}")
        return []

def get_custom_labels(bucket, key):
    """
    Retrieve custom labels from S3 object metadata
    
    :param bucket: S3 bucket name
    :param key: S3 object key
    :return: List of custom labels
    """
    try:
        # Retrieve object metadata
        head_response = s3_client.head_object(Bucket=bucket, Key=key)
        
        # Check for custom labels metadata
        custom_labels_str = head_response.get('Metadata', {}).get('customlabels', '')
        
        # Split and clean custom labels
        if custom_labels_str:
            return [label.strip().lower() for label in custom_labels_str.split(',') if label.strip()]
        return []
    except Exception as e:
        print(f"Error retrieving custom labels: {e}")
        return []

def index_photo(bucket, key):
    """
    Index photo in Elasticsearch
    
    :param bucket: S3 bucket name
    :param key: S3 object key
    """
    try:
        # Get object metadata
        head_response = s3_client.head_object(Bucket=bucket, Key=key)
        created_timestamp = head_response.get('LastModified').isoformat()
        
        # Detect Rekognition labels
        rekognition_labels = detect_image_labels(bucket, key)
        
        # Get custom labels
        custom_labels = get_custom_labels(bucket, key)
        
        # Combine labels
        all_labels = list(set(rekognition_labels + custom_labels))
        
        # Prepare Elasticsearch document
        document = {
            'objectKey': key,
            'bucket': bucket,
            'createdTimestamp': created_timestamp,
            'labels': all_labels
        }
        
        # Connect to Elasticsearch and index document
        es = connect_elasticsearch()
        es.index(index=INDEX, body=document)
        
        print(f"Indexed photo: {key} with labels: {all_labels}")
        return document
    except Exception as e:
        print(f"Error indexing photo {key}: {e}")
        raise

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
            
            # Validate file type (optional - add more image extensions if needed)
            if not key.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                print(f"Skipping non-image file: {key}")
                continue
            
            # Index the photo
            result = index_photo(bucket, key)
            
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

if __name__ == "__main__":
    bucket = "b2-buckett"
    key = "test-photo.jpg"
            
            # Validate file type (optional - add more image extensions if needed)
    if not key.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        print(f"Skipping non-image file: {key}")
            
            # Index the photo
    result = index_photo(bucket, key)
    print(result)
    print('Photo indexing completed successfully')
    