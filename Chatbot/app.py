
import streamlit as st
from typing import Optional
import sys

from config import Config, get_config
from services.gemini_service import GeminiService
from memory.session_memory import SessionMemory
from prompts.system_prompt import SystemPrompt
from utils.logger import ChatbotLogger


def configure_page():
    st.set_page_config(
        page_title=Config.APP_NAME,
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stChatMessage {
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .stChatMessage[data-role="user"] {
            background-color: #e3f2fd;
        }
        .stChatMessage[data-role="assistant"] {
            background-color: #f5f5f5;
        }
        .header-text {
            color: #1976d2;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)


def initialize_session_state():
    if "session_memory" not in st.session_state:
        st.session_state.session_memory = SessionMemory()
    
    if "gemini_service" not in st.session_state:
        try:
            st.session_state.gemini_service = GeminiService()
            st.session_state.api_connected = True
        except Exception as e:
            st.session_state.gemini_service = None
            st.session_state.api_connected = False
            logger = ChatbotLogger.get_logger(__name__)
            logger.error(f"Failed to initialize GeminiService: {str(e)}")
    
    if "logger" not in st.session_state:
        st.session_state.logger = ChatbotLogger.get_logger(__name__)
    
    if "response_generated" not in st.session_state:
        st.session_state.response_generated = False


def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Settings & Help")
        
        # Session Statistics
        st.markdown("### 📊 Session Statistics")
        stats = st.session_state.session_memory.get_session_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", stats["total_messages"])
            st.metric("Duration (s)", int(stats["session_duration_seconds"]))
        with col2:
            st.metric("User Msgs", stats["user_messages"])
            st.metric("Characters", stats["total_characters"])
        
        # API Status
        st.markdown("### 🔌 API Status")
        if st.session_state.api_connected:
            st.success("✅ Connected to Gemini API")
            if st.session_state.gemini_service:
                model_info = st.session_state.gemini_service.get_model_info()
                st.caption(f"Model: {model_info['model']}")
                st.caption(f"Temperature: {model_info['temperature']}")
        else:
            st.error("❌ Disconnected from Gemini API")
            st.warning("Check your GEMINI_API_KEY in .env file")
        
        # Test Connection Button
        if st.button("Test API Connection", use_container_width=True):
            with st.spinner("Testing connection..."):
                is_connected = GeminiService.test_connection()
                if is_connected:
                    st.success("Connection test passed!")
                    st.session_state.api_connected = True
                else:
                    st.error("Connection test failed!")
                    st.session_state.api_connected = False
        
        # Conversation Management
        st.markdown("### 🗑️ Conversation Management")
        
        if st.button("Clear History", use_container_width=True):
            st.session_state.session_memory.clear_history()
            st.success("Conversation history cleared")
            st.rerun()
        
        # Export Conversation
        if st.session_state.session_memory.messages:
            if st.button("Export Conversation", use_container_width=True):
                conversation_data = st.session_state.session_memory.export_conversation()
                st.download_button(
                    label="Download as JSON",
                    data=str(conversation_data),
                    file_name="conversation.json",
                    mime="application/json"
                )
        
        # Help Section
        st.markdown("### ❓ About This Chatbot")
        st.info(
            "This is your **Career Advisor AI Assistant** powered by Google Gemini. "
            "Ask about:\n"
            "• Career planning and goal setting\n"
            "• Skill development strategies\n"
            "• Job search optimization\n"
            "• Interview preparation\n"
            "• Career transitions\n"
            "• Leadership development"
        )
        
        # Model Configuration
        st.markdown("### ⚙️ Model Configuration")
        st.caption(f"Model: {Config.GEMINI_MODEL}")
        st.caption(f"Max Tokens: {Config.MAX_TOKENS}")
        st.caption(f"Temperature: {Config.TEMPERATURE}")


def render_chat_interface():
    
    st.markdown(
        f"<h1 style='text-align: center; color: #1976d2;'>💼 {Config.APP_NAME}</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align: center; color: #666;'>{Config.APP_DESCRIPTION}</p>",
        unsafe_allow_html=True
    )
    
    st.divider()
    
    render_conversation_history()
    
    st.divider()

    render_input_area()


def render_conversation_history():
    history = st.session_state.session_memory.get_conversation_history()
    
    if not history:
        st.info("👋 Welcome! Start a conversation by asking a career-related question.")
        return

    for msg in history:
        with st.chat_message(msg["role"], avatar="👨‍💼" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])


def render_input_area():
    
    if not st.session_state.api_connected:
        st.error(
            "⚠️ Cannot process requests - API connection unavailable. "
            "Please check your configuration."
        )
        st.stop()

    user_input = st.chat_input(
        placeholder="Ask me about your career...",
        key="user_input"
    )
    
    if user_input and user_input.strip():
        st.session_state.session_memory.add_user_message(user_input)

        with st.chat_message("user", avatar="👨‍💼"):
            st.markdown(user_input)
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔄 Thinking..."):
                response = get_assistant_response()
            
            if response:
                st.markdown(response)
                st.session_state.session_memory.add_assistant_message(response)
            else:
                st.error("Failed to generate response. Please try again.")
        
        st.session_state.session_memory.optimize_memory()
        st.rerun()


def get_assistant_response() -> Optional[str]:
    try:
        conversation_history = st.session_state.session_memory.get_conversation_history()
        
        system_prompt = SystemPrompt.get_system_prompt()
        
        response = st.session_state.gemini_service.send_message(
            conversation_history=conversation_history,
            system_prompt=system_prompt
        )
        
        if response and st.session_state.gemini_service.validate_response(response):
            user_msg = st.session_state.session_memory.messages[-1].content
            st.session_state.logger.info(
                f"Successfully generated response. "
                f"User message: {len(user_msg)} chars, "
                f"Response: {len(response)} chars"
            )
            return response
        else:
            st.session_state.logger.warning("Invalid or empty response received")
            return None
    
    except Exception as e:
        st.session_state.logger.error(f"Error generating response: {str(e)}")
        return None



def validate_configuration():
    try:
        config = get_config()
        return True
    except ValueError as e:
        st.error(f"⚠️ Configuration Error: {str(e)}")
        st.stop()
        return False



def main():
    
    configure_page()
    
    if not validate_configuration():
        return
    
    initialize_session_state()
    
    render_sidebar()
    render_chat_interface()


if __name__ == "__main__":
    main()
