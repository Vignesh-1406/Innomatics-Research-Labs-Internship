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


class BedrockKBSetup:
    
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-agent', region_name=AWS_REGION)
        self.iam_client = boto3.client('iam')
        self.sts_client = boto3.client('sts', region_name=AWS_REGION)
        print(f"Bedrock client initialized in region: {AWS_REGION}")
    
    def get_account_id(self):
        try:
            response = self.sts_client.get_caller_identity()
            return response['Account']
        except ClientError as e:
            print(f"Error getting account ID: {e}")
            return None
    
    def get_iam_role_arn(self, role_name='BedrockKnowledgeBaseRole'):
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except ClientError as e:
            print(f"IAM role not found: {role_name}")
            print(f"Please create IAM role first: {e}")
            return None
    
    def create_knowledge_base(self, role_arn, collection_arn):
        try:
            response = self.bedrock_client.create_knowledge_base(
                name=KNOWLEDGE_BASE_NAME,
                description='RAG Knowledge Base for Document Q&A',
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/{EMBEDDING_MODEL}'
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': collection_arn
                    }
                }
            )
            kb_id = response['knowledgeBase']['id']
            print(f"Knowledge Base created: {kb_id}")
            return kb_id
        except ClientError as e:
            if 'already exists' in str(e):
                print(f"Knowledge Base already exists")
                kb = self.get_knowledge_base_by_name(KNOWLEDGE_BASE_NAME)
                return kb['id'] if kb else None
            print(f"Error creating Knowledge Base: {e}")
            return None
    
    def get_knowledge_base_by_name(self, name):
        try:
            response = self.bedrock_client.list_knowledge_bases()
            for kb in response.get('knowledgeBaseSummaries', []):
                if kb['name'] == name:
                    return kb
            return None
        except ClientError as e:
            print(f"Error listing Knowledge Bases: {e}")
            return None
    
    def create_data_source(self, kb_id):
        try:
            response = self.bedrock_client.create_data_source(
                knowledgeBaseId=kb_id,
                name=f'{KNOWLEDGE_BASE_NAME}-datasource',
                description='Document data source from S3',
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{S3_BUCKET_NAME}',
                        'inclusionPrefixes': [S3_DATA_PREFIX]
                    }
                }
            )
            ds_id = response['dataSource']['id']
            print(f"Data source created: {ds_id}")
            return ds_id
        except ClientError as e:
            print(f"Error creating data source: {e}")
            return None
    
    def start_ingestion_job(self, kb_id, ds_id):
        try:
            response = self.bedrock_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id
            )
            job_id = response['ingestionJob']['id']
            print(f"Ingestion job started: {job_id}")
            return job_id
        except ClientError as e:
            print(f"Error starting ingestion job: {e}")
            return None
    
    def wait_for_ingestion(self, kb_id, ds_id, job_id, max_wait=600):
        print("Waiting for ingestion to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.bedrock_client.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id,
                    ingestionJobId=job_id
                )
                status = response['ingestionJob']['status']
                print(f"Ingestion status: {status}")
                
                if status in ['COMPLETE', 'FAILED']:
                    return status == 'COMPLETE'
                
                time.sleep(10)
            except ClientError as e:
                print(f"Error checking ingestion status: {e}")
                return False
        
        print("Ingestion timeout")
        return False
    
    def setup_complete(self, role_arn, collection_arn):
        print("\n" + "="*60)
        print("Bedrock Knowledge Base Setup")
        print("="*60 + "\n")
        
        kb_id = self.create_knowledge_base(role_arn, collection_arn)
        if not kb_id:
            print("Failed to create Knowledge Base")
            return False
        
        ds_id = self.create_data_source(kb_id)
        if not ds_id:
            print("Failed to create data source")
            return False
        
        job_id = self.start_ingestion_job(kb_id, ds_id)
        if not job_id:
            print("Failed to start ingestion job")
            return False
        
        success = self.wait_for_ingestion(kb_id, ds_id, job_id)
        
        print("\n" + "="*60)
        print("Setup Summary")
        print("="*60)
        print(f"Knowledge Base ID: {kb_id}")
        print(f"Data Source ID: {ds_id}")
        print(f"Ingestion Job ID: {job_id}")
        print(f"Status: {'Success' if success else 'Failed'}")
        print(f"\nUpdate bedrock_config.py with:")
        print(f"KNOWLEDGE_BASE_ID = '{kb_id}'")
        
        return success


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python aws_bedrock_kb_setup.py <iam_role_arn> <opensearch_collection_arn>")
        sys.exit(1)
    
    role_arn = sys.argv[1]
    collection_arn = sys.argv[2]
    
    setup = BedrockKBSetup()
    setup.setup_complete(role_arn, collection_arn)
