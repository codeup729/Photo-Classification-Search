import json
import boto3
import requests
from requests_aws4auth import AWS4Auth

# OpenSearch Configuration
opensearch_host = 'https://search-photos-xpic4374vmunyumswyzwftvsyi.aos.us-east-1.on.aws'  # Replace with your OpenSearch endpoint
index_name = 'photos'

# AWS Credentials and Region
AWS_ACCESS_KEY = 'AKIAQZFG5JYFOWX7IPWN'
AWS_SECRET_KEY = 'cUYO45lmYXiV9CznJiVLvM5HvJaVv165xYs2Q5kq'
REGION = 'us-east-1' 

# AWS SigV4 Authentication
awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION, 'es')

# Initialize AWS Lex Client
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

def lambda_handler(event, context):
    """
    Lambda function to handle Lex queries and search OpenSearch index.
    """
    try:
        # Extract the query from the input event
        query = event.get('q', '')
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

        # Extract keywords from the Lex slot (Category)
        slots = response.get('interpretations', [{}])[0].get('intent', {}).get('slots', {})
        category_slot = slots.get('Category', {}).get('value', {}).get('interpretedValue', '')

        # If Category slot is filled, search OpenSearch
        if category_slot:
            keywords = category_slot.split()  # Split into individual keywords if multiple
            photos = search_photos_in_opensearch(keywords)
            return {
                "statusCode": 200,
                "body": json.dumps({"results": photos})
            }
        else:
            # No keywords found, return empty results
            return {
                "statusCode": 200,
                "body": json.dumps({"results": []})
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
        "q": "show me photos of bird"
    }
    response = lambda_handler(mock_event, None)
    print(json.dumps(response, indent=2))
