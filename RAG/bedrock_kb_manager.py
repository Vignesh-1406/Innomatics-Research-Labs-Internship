import boto3
import time
from botocore.exceptions import ClientError
from bedrock_config import (
    AWS_REGION, 
    S3_BUCKET_NAME, 
    S3_DATA_PREFIX, 
    KNOWLEDGE_BASE_NAME,
    EMBEDDING_MODEL
)


class BedrockKnowledgeBaseManager:
    
    def __init__(self):
        try:
            self.client = boto3.client('bedrock-agent', region_name=AWS_REGION)
            print(f"Bedrock Agent client initialized in region: {AWS_REGION}")
        except ClientError as e:
            print(f"Error initializing Bedrock Agent client: {e}")
            raise
    
    def create_knowledge_base(self, name: str = KNOWLEDGE_BASE_NAME, 
                             s3_bucket: str = S3_BUCKET_NAME,
                             s3_prefix: str = S3_DATA_PREFIX) -> str:
        try:
            response = self.client.create_knowledge_base(
                name=name,
                description='RAG Knowledge Base for NexaTech Solutions',
                roleArn=self._get_iam_role_arn(),
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/{EMBEDDING_MODEL}'
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': self._get_or_create_collection_arn()
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['id']
            print(f"Knowledge Base created: {kb_id}")
            return kb_id
            
        except ClientError as e:
            if 'already exists' in str(e):
                print(f"Knowledge Base already exists")
                kb_id = self.get_knowledge_base_by_name(name)
                return kb_id
            print(f"Error creating knowledge base: {e}")
            return None
    
    def create_data_source(self, kb_id: str, s3_bucket: str = S3_BUCKET_NAME,
                          s3_prefix: str = S3_DATA_PREFIX) -> str:
        try:
            response = self.client.create_data_source(
                knowledgeBaseId=kb_id,
                name=f'nexatech-datasource',
                description='NexaTech Documents Data Source',
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{s3_bucket}',
                        'inclusionPrefixes': [s3_prefix]
                    }
                }
            )
            
            ds_id = response['dataSource']['id']
            print(f"Data source created: {ds_id}")
            return ds_id
            
        except ClientError as e:
            print(f"Error creating data source: {e}")
            return None
    
    def sync_data_source(self, kb_id: str, ds_id: str) -> bool:
        try:
            response = self.client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id
            )
            
            job_id = response['ingestionJob']['id']
            print(f"Ingestion job started: {job_id}")
            print("This may take a few minutes to complete...")
            
            self._wait_for_ingestion_job(kb_id, ds_id, job_id)
            return True
            
        except ClientError as e:
            print(f"Error starting ingestion job: {e}")
            return False
    
    def _wait_for_ingestion_job(self, kb_id: str, ds_id: str, job_id: str, 
                               max_wait: int = 600):
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.client.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id,
                    ingestionJobId=job_id
                )
                
                status = response['ingestionJob']['status']
                print(f"Job status: {status}")
                
                if status in ['COMPLETE', 'FAILED']:
                    if status == 'COMPLETE':
                        print("Ingestion job completed successfully")
                    else:
                        print("Ingestion job failed")
                    return
                
                time.sleep(10)
                
            except ClientError as e:
                print(f"Error checking job status: {e}")
                return
    
    def list_knowledge_bases(self) -> list:
        try:
            response = self.client.list_knowledge_bases()
            kbs = response.get('knowledgeBaseSummaries', [])
            print(f"Found {len(kbs)} knowledge base(s)")
            
            for kb in kbs:
                print(f"  - {kb['name']} (ID: {kb['id']})")
            
            return kbs
        except ClientError as e:
            print(f"Error listing knowledge bases: {e}")
            return []
    
    def get_knowledge_base_by_name(self, name: str) -> str:
        kbs = self.list_knowledge_bases()
        for kb in kbs:
            if kb['name'] == name:
                return kb['id']
        return None
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        try:
            self.client.delete_knowledge_base(knowledgeBaseId=kb_id)
            print(f"Knowledge base {kb_id} deleted")
            return True
        except ClientError as e:
            print(f"Error deleting knowledge base: {e}")
            return False
    
    def _get_iam_role_arn(self) -> str:
        return "arn:aws:iam::YOUR_ACCOUNT_ID:role/BedrockKnowledgeBaseRole"
    
    def _get_or_create_collection_arn(self) -> str:
        return "arn:aws:aoss:YOUR_REGION:YOUR_ACCOUNT_ID:collection/YOUR_COLLECTION_ID"


def create_kb_manager() -> BedrockKnowledgeBaseManager:
    return BedrockKnowledgeBaseManager()
