import argparse
import sys
from bedrock_kb_handler import create_bedrock_handler
from bedrock_kb_manager import create_kb_manager
from s3_handler import create_s3_handler
from bedrock_config import KNOWLEDGE_BASE_ID, S3_BUCKET_NAME


def query_command(args):
    print("\n" + "="*60)
    print("AWS Bedrock RAG Query")
    print("="*60 + "\n")
    
    handler = create_bedrock_handler()
    result = handler.retrieve_and_answer(args.query)
    
    print(f"\nQuery: {result['query']}\n")
    print("Answer:")
    print("-" * 60)
    print(result['answer'])
    print("-" * 60)
    
    print(f"\nRetrieved {len(result['retrieved_documents'])} document(s):\n")
    
    for i, doc in enumerate(result['retrieved_documents'], 1):
        print(f"Document {i}:")
        print(f"  Source: {doc['source']}")
        print(f"  Score: {doc['score']:.2%}")
        print(f"  Content: {doc['content'][:200]}...")
        print()


def setup_command(args):
    print("\n" + "="*60)
    print("AWS Bedrock RAG Setup")
    print("="*60 + "\n")
    
    s3_handler = create_s3_handler()
    
    print("Creating S3 bucket...")
    if s3_handler.create_bucket():
        print("S3 bucket ready\n")
    
    if args.documents:
        print(f"Uploading documents from: {args.documents}")
        count = s3_handler.upload_directory(args.documents)
        print(f"{count} documents uploaded\n")
    
    print("Documents in S3:")
    docs = s3_handler.list_documents()
    for doc in docs:
        print(f"  - {doc}")


def kb_command(args):
    manager = create_kb_manager()
    
    if args.kb_action == 'create':
        print("\nCreating Knowledge Base...")
        kb_id = manager.create_knowledge_base()
        if kb_id:
            print(f"Knowledge Base ID: {kb_id}")
            print(f"Add to bedrock_config.py: KNOWLEDGE_BASE_ID = '{kb_id}'")
    
    elif args.kb_action == 'list':
        print("\nListing Knowledge Bases:")
        manager.list_knowledge_bases()
    
    elif args.kb_action == 'sync':
        print(f"\nSyncing Knowledge Base: {KNOWLEDGE_BASE_ID}")
        print("Usage: first create data source, then run: kb_id=xxx ds_id=yyy")
    
    elif args.kb_action == 'delete':
        if args.kb_id:
            confirm = input(f"Delete KB {args.kb_id}? (yes/no): ")
            if confirm.lower() == 'yes':
                manager.delete_knowledge_base(args.kb_id)


def init_command(args):
    print("\n" + "="*60)
    print("AWS Bedrock RAG - Initial Setup")
    print("="*60 + "\n")
    
    print("Step 1: Uploading documents to S3...")
    s3_handler = create_s3_handler()
    if s3_handler.create_bucket():
        if args.documents:
            s3_handler.upload_directory(args.documents)
    
    print("\nStep 2: Creating Knowledge Base...")
    manager = create_kb_manager()
    kb_id = manager.create_knowledge_base()
    
    if kb_id:
        print("\nStep 3: Creating data source...")
        ds_id = manager.create_data_source(kb_id)
        
        if ds_id:
            print("\nStep 4: Syncing data source...")
            manager.sync_data_source(kb_id, ds_id)
            
            print("\n" + "="*60)
            print("Setup Complete!")
            print("="*60)
            print(f"Knowledge Base ID: {kb_id}")
            print(f"Data Source ID: {ds_id}")
            print(f"\nUpdate bedrock_config.py:")
            print(f"  KNOWLEDGE_BASE_ID = '{kb_id}'")


def main():
    parser = argparse.ArgumentParser(
        description="AWS Bedrock Knowledge Base RAG System CLI"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    query_parser = subparsers.add_parser('query', help='Query the knowledge base')
    query_parser.add_argument('query', help='Your question')
    query_parser.add_argument('--top-k', type=int, default=3, help='Number of documents to retrieve')
    query_parser.set_defaults(func=query_command)
    
    setup_parser = subparsers.add_parser('setup', help='Setup S3 and upload documents')
    setup_parser.add_argument('--documents', default='data', help='Directory containing documents')
    setup_parser.set_defaults(func=setup_command)
    
    kb_parser = subparsers.add_parser('kb', help='Manage Knowledge Base')
    kb_parser.add_argument('kb_action', choices=['create', 'list', 'sync', 'delete'])
    kb_parser.add_argument('--kb-id', help='Knowledge Base ID (for delete)')
    kb_parser.set_defaults(func=kb_command)
    
    init_parser = subparsers.add_parser('init', help='Complete setup')
    init_parser.add_argument('--documents', default='data', help='Directory containing documents')
    init_parser.set_defaults(func=init_command)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
