from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import os
from dotenv import load_dotenv
import certifi
import boto3

load_dotenv()


host = os.getenv('OPENSEARCH_HOST')
port = os.getenv('OPENSEARCH_PORT')
region = 'us-east-1'

service = 'aoss'
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, service)


# Create the client with SSL/TLS enabled, but hostname verification disabled.
client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_compress = True, # enables gzip compression for request bodies
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    pool_maxsize=20,
)

index_name = "comments"

query = {
    "size": 0,  # No need to fetch individual documents
    "aggs": {
        "docketId_stats": {
            "terms": {
                "field": "docketId.keyword",  # Use .keyword for exact match on text fields
                "size": 1000  # Adjust size for expected number of unique docketIds
            },
            "aggs": {
                "matching_comments": {
                    "filter": {
                        "match": {
                            "comment": "drug"
                        }
                    }
                }
            }
        }
    }
}

# Execute the query
response = client.search(index=index_name, body=query)

# Extract the aggregation results
dockets = response["aggregations"]["docketId_stats"]["buckets"]

# Get the total number of documents in the index
index_stats = client.count(index=index_name)
total_documents = index_stats["count"]

# Print the report
print("Report: Matches and Total Comments Per Docket")
for docket in dockets:
    docket_id = docket["key"]
    total_comments = docket["doc_count"]
    matching_comments = docket["matching_comments"]["doc_count"]
    print(f"docketId: {docket_id}, Matches: {matching_comments}, Total Comments: {total_comments}")

print(f"\nTotal number of documents in the index: {total_documents}")