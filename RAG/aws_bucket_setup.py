import boto3
import json
from botocore.exceptions import ClientError
from bedrock_config import AWS_REGION, S3_BUCKET_NAME, S3_DATA_PREFIX


class AWSBucketSetup:
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        print(f"S3 client initialized in region: {AWS_REGION}")
    
    def create_s3_bucket(self):
        try:
            self.s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"Bucket {S3_BUCKET_NAME} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    if AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=S3_BUCKET_NAME,
                            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                        )
                    print(f"Bucket {S3_BUCKET_NAME} created successfully")
                    return True
                except ClientError as e:
                    print(f"Error creating bucket: {e}")
                    return False
            return False
    
    def enable_versioning(self):
        try:
            self.s3_client.put_bucket_versioning(
                Bucket=S3_BUCKET_NAME,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            print(f"Versioning enabled for {S3_BUCKET_NAME}")
            return True
        except ClientError as e:
            print(f"Error enabling versioning: {e}")
            return False
    
    def set_bucket_policy(self):
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/{S3_DATA_PREFIX}*",
                    "Condition": {
                        "StringEquals": {
                            "aws:PrincipalAccount": boto3.client('sts',  region_name=AWS_REGION).get_caller_identity()['Account']
                        }
                    }
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_policy(
                Bucket=S3_BUCKET_NAME,
                Policy=json.dumps(bucket_policy)
            )
            print(f"Bucket policy set for {S3_BUCKET_NAME}")
            return True
        except ClientError as e:
            print(f"Error setting bucket policy: {e}")
            return False
    
    def apply_lifecycle_policy(self):
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'ArchiveOldDocuments',
                    'Status': 'Enabled',
                    'Prefix': S3_DATA_PREFIX,
                    'Transitions': [
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        }
                    ],
                    'Expiration': {
                        'Days': 365
                    }
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=S3_BUCKET_NAME,
                LifecycleConfiguration=lifecycle_config
            )
            print(f"Lifecycle policy applied to {S3_BUCKET_NAME}")
            return True
        except ClientError as e:
            print(f"Error applying lifecycle policy: {e}")
            return False
    
    def setup_complete(self):
        print("\n" + "="*60)
        print("S3 Bucket Setup Summary")
        print("="*60)
        
        success = True
        success &= self.create_s3_bucket()
        success &= self.enable_versioning()
        success &= self.set_bucket_policy()
        success &= self.apply_lifecycle_policy()
        
        if success:
            print("\nS3 bucket setup completed successfully!")
            print(f"Bucket URL: s3://{S3_BUCKET_NAME}/{S3_DATA_PREFIX}")
        else:
            print("\nSome setup steps failed. Check errors above.")
        
        return success


if __name__ == '__main__':
    setup = AWSBucketSetup()
    setup.setup_complete()
