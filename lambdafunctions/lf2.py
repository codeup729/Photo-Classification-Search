import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
import base64  # Ensure this is imported
import os

# OpenSearch Configuration
opensearch_host = 'https://search-photos-xpic4374vmunyumswyzwftvsyi.aos.us-east-1.on.aws'  # Replace with your OpenSearch endpoint
index_name = 'photos'

# AWS Credentials and Region
AWS_ACCESS_KEY = 'AKIAQZFG5JYFOWX7IPWN'
AWS_SECRET_KEY = 'cUYO45lmYXiV9CznJiVLvM5HvJaVv165xYs2Q5kq'
REGION = 'us-east-1' 

# AWS SigV4 Authentication
awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=REGION)
lex_client = boto3.client('lexv2-runtime', region_name=REGION)


def search_photos_in_opensearch(keywords):
    """
    Query OpenSearch index with keywords.
    """
    query = {
        "query": {
            "bool": {
                "should": [{"match": {"labels": keyword}} for keyword in keywords]
            }
        }
    }

    url = f"{opensearch_host}/{index_name}/_search"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, auth=awsauth, headers=headers, data=json.dumps(query))
        if response.status_code == 200:
            results = response.json()
            photos = [hit["_source"] for hit in results["hits"]["hits"]]
            return photos
        else:
            print(f"OpenSearch query failed: {response.text}")
            return []
    except Exception as e:
        print(f"Error querying OpenSearch: {e}")
        return []


def get_image_from_s3(bucket, object_key):
    """
    Download image from S3 and return its Base64-encoded content.
    """
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=object_key)
        image_data = response['Body'].read()
        
        # Encode the image as Base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        return encoded_image
    except Exception as e:
        print(f"Error fetching image from S3: {e}")
        return None


def lambda_handler(event, context):
    """
    Lambda function to handle Lex queries and search OpenSearch index.
    """
    try:
        # Log the incoming event for debugging
        print("Received event:", json.dumps(event))

        # Extract the query from the input event
        query = event.get('queryStringParameters', {}).get('q', None)
        if not query:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing query parameter 'q'"})
            }

        # Call Lex to process the query
        response = lex_client.recognize_text(
            botId='DFU3YIZX0Y',       # Replace with your Lex bot ID
            botAliasId='TSTALIASID',  # Replace with your Lex bot alias ID
            localeId='en_US',
            sessionId='search-session',
            text=query
        )

        print("Lex response:", json.dumps(response))  # Log the Lex response

        # Extract keywords from the Lex slot (Category)
        interpretations = response.get('interpretations', [])
        if interpretations:
            intent = interpretations[0].get('intent', {})
            slots = intent.get('slots', {})
            category_slot = slots.get('Category', {}).get('value', {}).get('interpretedValue', None)
        else:
            category_slot = None

        print("Extracted category slot:", category_slot)

        # If Category slot is filled, search OpenSearch
        if category_slot:
            keywords = category_slot.split()  # Split into individual keywords if multiple
            photos = search_photos_in_opensearch(keywords)

            # If photos are found, get the image from S3
            if photos:
                photo = photos[0]  # Get the first photo (modify if multiple photos are required)
                bucket = photo['bucket']
                object_key = photo['objectKey']

                # Fetch and encode the image from S3
                encoded_image = get_image_from_s3(bucket, object_key)
                if encoded_image:
                    print(encoded_image)
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "image": encoded_image,
                            "bucket": bucket,
                            "objectKey": object_key,
                            "labels": photo['labels']
                        })
                    }
                else:
                    return {
                        "statusCode": 500,
                        "body": json.dumps({"error": "Failed to fetch image from S3."})
                    }
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "No matching photos found."})
                }
        else:
            # No keywords found, return empty results
            return {
                "statusCode": 200,
                "body": json.dumps({"results": [], "message": "No valid category specified."})
            }

    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
# Main Execution for Testing
if __name__ == "__main__":
    # Mock input for testing
    mock_event = {
        "q": "show me photos of cat"
    }
    response = lambda_handler(mock_event, None)
    print(json.dumps(response, indent=2))
