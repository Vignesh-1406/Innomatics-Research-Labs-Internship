import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'your-rag-bucket')
S3_DATA_PREFIX = os.getenv('S3_DATA_PREFIX', 'documents/')

KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')
KNOWLEDGE_BASE_NAME = os.getenv('KNOWLEDGE_BASE_NAME', 'NexaTech-RAG-KB')

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 3

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')
