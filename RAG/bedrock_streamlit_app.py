import streamlit as st
from bedrock_kb_handler import create_bedrock_handler
from bedrock_config import KNOWLEDGE_BASE_ID

st.set_page_config(page_title="Bedrock RAG QA System", layout="wide")

st.title("AWS Bedrock Knowledge Base RAG System")
st.markdown("**Powered by AWS Bedrock & S3**")

if 'kb_handler' not in st.session_state:
    st.session_state.kb_handler = create_bedrock_handler()

with st.sidebar:
    st.header("Configuration")
    st.info(f"Knowledge Base ID: `{KNOWLEDGE_BASE_ID}`")
    
    top_k = st.slider(
        "Number of documents to retrieve",
        min_value=1,
        max_value=10,
        value=3
    )
    
    st.divider()
    st.markdown("### About")
    st.write("""
    This RAG system uses:
    - **AWS Bedrock** for LLM and embeddings
    - **S3** for document storage
    - **Knowledge Base** for semantic search
    """)

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    user_query = st.text_area(
        "Enter your question:",
        placeholder="What is the company policy on remote work?",
        height=100
    )

with col2:
    st.markdown("### Quick Actions")
    ask_button = st.button("Ask", use_container_width=True, type="primary")
    clear_button = st.button("Clear", use_container_width=True)

if ask_button and user_query:
    with st.spinner("Retrieving documents and generating answer..."):
        try:
            result = st.session_state.kb_handler.retrieve_and_answer(user_query)
            
            st.markdown("---")
            st.markdown("### Answer")
            st.markdown(f"""
            <div style="background-color:#f0f2f6; padding:15px; border-radius:5px;">
            {result['answer']}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### Retrieved Context")
            
            if result['retrieved_documents']:
                for i, doc in enumerate(result['retrieved_documents'], 1):
                    with st.expander(f"Document {i} (Score: {doc['score']:.2%})"):
                        st.markdown(f"**Source:** {doc['source']}")
                        st.text(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
            else:
                st.warning("No relevant documents found.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Make sure your AWS credentials and Knowledge Base ID are configured correctly.")

elif clear_button:
    st.rerun()

elif not user_query and ask_button:
    st.warning("Please enter a question first.")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8em;">
Built with Streamlit | Powered by AWS Bedrock
</div>
""", unsafe_allow_html=True)
