# AWS Bedrock Knowledge Base RAG System

Retrieval-Augmented Generation (RAG) system using AWS Bedrock Knowledge Base for semantic search and document Q&A.

## Features

- AWS Bedrock integration with Claude 3 LLM
- S3 document storage and management
- Semantic search via Bedrock Knowledge Base
- Streamlit web interface for queries
- CLI for document upload and KB management
- EC2 deployment support
- OpenSearch Serverless vector storage

## Architecture

```
User Query
    ↓
Bedrock Knowledge Base (Semantic Search)
    ↓
S3 Document Retrieval
    ↓
Claude 3 LLM (Answer Generation)
    ↓
Answer + Source Documents
```

## Prerequisites

- AWS Account with Bedrock access
- Python 3.8+
- AWS CLI configured with credentials
- IAM role with Bedrock/S3/OpenSearch permissions

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r bedrock_requirements.txt
   ```

3. Create .env file from .env.example:
   ```bash
   cp .env.example .env
   ```

4. Configure AWS credentials:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_REGION=us-east-1
   ```

## Setup

### Step 1: Create S3 Bucket
```bash
python aws_bucket_setup.py
```

### Step 2: Create Bedrock Knowledge Base
First, create IAM role and OpenSearch collection manually, then:
```bash
python aws_bedrock_kb_setup.py <IAM_ROLE_ARN> <OPENSEARCH_COLLECTION_ARN>
```

### Step 3: Upload Documents
Place .txt files in `data/` folder, then:
```bash
python bedrock_cli.py setup --documents data
```

## Usage

### Command Line
```bash
python bedrock_cli.py query "What is the remote work policy?"
python bedrock_cli.py setup --documents data
python bedrock_cli.py kb list
python bedrock_cli.py kb create
```

### Web Interface
```bash
streamlit run bedrock_streamlit_app.py
```
Access at: `http://localhost:8501`

### EC2 Deployment
```bash
bash ec2_deploy.sh deploy
bash ec2_deploy.sh cleanup
```

## Project Structure

```
├── bedrock_config.py              Configuration management
├── bedrock_kb_handler.py          Core RAG logic
├── bedrock_kb_manager.py          KB lifecycle management
├── s3_handler.py                  S3 operations
├── bedrock_cli.py                 CLI interface
├── bedrock_streamlit_app.py       Web UI
├── aws_bucket_setup.py            S3 setup
├── aws_bedrock_kb_setup.py        KB setup
├── ec2_deploy.sh                  EC2 deployment
├── bedrock_requirements.txt       Dependencies
├── .env.example                   Environment template
└── data/                          Document storage
```

## Configuration

Edit `.env`:
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your-bucket
KNOWLEDGE_BASE_ID=kb_xxxxx
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## AWS IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "s3:*",
        "opensearchserverless:*",
        "iam:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Cost Optimization

- S3: ~$0.023/GB/month
- Bedrock: ~$0.003 per 1k tokens
- OpenSearch Serverless: ~$1.4/hour
- Monthly estimate: $50-100 for small KB

## Troubleshooting

| Issue | Solution |
|-------|----------|
| AWS credentials not found | Run `aws configure` |
| Bedrock model not available | Enable model in Bedrock console |
| Knowledge Base not found | Check KNOWLEDGE_BASE_ID in .env |
| S3 access denied | Verify IAM permissions |

## API Reference

### BedrockKBHandler
```python
from bedrock_kb_handler import create_bedrock_handler

handler = create_bedrock_handler()
result = handler.retrieve_and_answer("Your question")
print(result['answer'])
```

### S3DocumentHandler
```python
from s3_handler import create_s3_handler

s3_handler = create_s3_handler()
s3_handler.upload_directory('data/')
docs = s3_handler.list_documents()
```

## Security

- Never commit .env file
- Use IAM roles for EC2 instances
- Enable S3 versioning
- Encrypt sensitive data
- Use private S3 bucket

## Performance

- Retrieve top-3 documents by default
- Chunk size: 1000 characters
- Embedding model: Amazon Titan
- LLM: Claude 3 Sonnet

## Deployment Options

1. **Local**: Development machine
2. **EC2**: Full control with bash script
3. **Streamlit Cloud**: Web UI only
4. **Lambda**: Serverless backend (custom setup)

## Maintenance

- Monitor S3 bucket size
- Review Bedrock API costs
- Archive old documents
- Update dependencies monthly

## Support

For issues or questions:
1. Check AWS Bedrock documentation
2. Review error messages in logs
3. Verify IAM permissions
4. Ensure AWS credentials are set

## License

Proprietary - For authorized use only

## Version

1.0.0 - April 2026
