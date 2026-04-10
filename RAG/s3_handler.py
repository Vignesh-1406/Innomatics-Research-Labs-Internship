import boto3
import os
from pathlib import Path
from botocore.exceptions import ClientError
from bedrock_config import AWS_REGION, S3_BUCKET_NAME, S3_DATA_PREFIX


class S3DocumentHandler:
    
    def __init__(self, bucket_name: str = S3_BUCKET_NAME):
        try:
            self.s3_client = boto3.client('s3', region_name=AWS_REGION)
            self.bucket_name = bucket_name
            print(f"S3 client initialized for bucket: {bucket_name}")
        except ClientError as e:
            print(f"Error initializing S3: {e}")
            raise
    
    def create_bucket(self) -> bool:
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"Bucket '{self.bucket_name}' created successfully")
                    return True
                except ClientError as create_error:
                    print(f"Error creating bucket: {create_error}")
                    return False
            else:
                print(f"Error checking bucket: {e}")
                return False
    
    def upload_document(self, file_path: str, s3_key: str = None) -> bool:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        if s3_key is None:
            s3_key = f"{S3_DATA_PREFIX}{os.path.basename(file_path)}"
        
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            print(f"Uploaded: {os.path.basename(file_path)} -> s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            print(f"Error uploading {file_path}: {e}")
            return False
    
    def upload_directory(self, directory_path: str) -> int:
        if not os.path.isdir(directory_path):
            print(f"Directory not found: {directory_path}")
            return 0
        
        uploaded_count = 0
        txt_files = list(Path(directory_path).glob('*.txt'))
        
        if not txt_files:
            print(f"No .txt files found in {directory_path}")
            return 0
        
        print(f"Uploading {len(txt_files)} files from {directory_path}...")
        for file_path in txt_files:
            if self.upload_document(str(file_path)):
                uploaded_count += 1
        
        print(f"Upload complete: {uploaded_count}/{len(txt_files)} files uploaded")
        return uploaded_count
    
    def list_documents(self) -> list:
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=S3_DATA_PREFIX
            )
            
            if 'Contents' not in response:
                print("No documents found in S3")
                return []
            
            documents = [obj['Key'] for obj in response['Contents']]
            print(f"Found {len(documents)} documents in S3")
            return documents
        except ClientError as e:
            print(f"Error listing documents: {e}")
            return []
    
    def delete_document(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"Deleted: {s3_key}")
            return True
        except ClientError as e:
            print(f"Error deleting {s3_key}: {e}")
            return False


def create_s3_handler(bucket_name: str = S3_BUCKET_NAME) -> S3DocumentHandler:
    return S3DocumentHandler(bucket_name)
