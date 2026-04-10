import boto3
import json
from botocore.exceptions import ClientError
from bedrock_config import (
    AWS_REGION, 
    KNOWLEDGE_BASE_ID, 
    BEDROCK_MODEL_ID, 
    TOP_K_RESULTS
)


class BedrockKBHandler:
    
    def __init__(self):
        try:
            self.bedrock_client = boto3.client(
                'bedrock-agent-runtime',
                region_name=AWS_REGION
            )
            self.bedrock_kb_client = boto3.client(
                'bedrock-agent',
                region_name=AWS_REGION
            )
            print(f"Connected to AWS Bedrock in region: {AWS_REGION}")
        except ClientError as e:
            print(f"Error connecting to Bedrock: {e}")
            raise
    
    def retrieve_documents(self, query: str, kb_id: str = KNOWLEDGE_BASE_ID) -> dict:
        try:
            response = self.bedrock_client.retrieve(
                knowledgeBaseId=kb_id,
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': TOP_K_RESULTS,
                        'overrideSearchType': 'SEMANTIC'
                    }
                },
                text=query
            )
            return response
        except ClientError as e:
            print(f"Error retrieving documents: {e}")
            return {'retrievalResults': []}
    
    def generate_answer(self, query: str, context: str) -> str:
        try:
            response = self.bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-06-01',
                    'max_tokens': 500,
                    'messages': [
                        {
                            'role': 'user',
                            'content': f"""Based on the following context, answer the question concisely.

Context:
{context}

Question: {query}

Answer:"""
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            answer = response_body['content'][0]['text']
            return answer
        except ClientError as e:
            print(f"Error generating answer: {e}")
            return "Unable to generate answer at this time."
    
    def retrieve_and_answer(self, query: str) -> dict:
        print(f"Retrieving documents for query: {query}")
        retrieval_response = self.retrieve_documents(query)
        
        context = ""
        retrieved_docs = []
        
        if 'retrievalResults' in retrieval_response:
            for i, result in enumerate(retrieval_response['retrievalResults']):
                content = result.get('content', {}).get('text', '')
                source = result.get('source', 'Unknown')
                score = result.get('score', 0)
                
                context += f"Document {i+1} (Score: {score:.2f}):\n{content}\n\n"
                retrieved_docs.append({
                    'source': source,
                    'content': content,
                    'score': score
                })
        
        if not context:
            return {
                'answer': 'No relevant documents found in the knowledge base.',
                'retrieved_documents': []
            }
        
        print(f"Generating answer from {len(retrieved_docs)} documents...")
        answer = self.generate_answer(query, context)
        
        return {
            'query': query,
            'answer': answer,
            'retrieved_documents': retrieved_docs
        }


def create_bedrock_handler():
    return BedrockKBHandler()
