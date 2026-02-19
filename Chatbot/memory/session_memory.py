
from typing import List, Dict, Tuple
from datetime import datetime
from config import Config
from utils.logger import ChatbotLogger


class ConversationMessage:
    
    def __init__(
        self,
        role: str,
        content: str,
        metadata: Dict = None
    ):
       
        self.role = role
        self.content = content
        self.timestamp = datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
    
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def get_formatted_text(self) -> str:
    
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.role.upper()}: {self.content}"


class SessionMemory:
    
    def __init__(self):
        self.messages: List[ConversationMessage] = []
        self.session_start = datetime.now()
        self.logger = ChatbotLogger.get_logger(__name__)
    
    def add_user_message(self, content: str, metadata: Dict = None):

        message = ConversationMessage("user", content, metadata)
        self.messages.append(message)
        self.logger.debug(f"Added user message: {len(content)} characters")
    
    def add_assistant_message(self, content: str, metadata: Dict = None):

        message = ConversationMessage("assistant", content, metadata)
        self.messages.append(message)
        self.logger.debug(f"Added assistant message: {len(content)} characters")
    
    def get_conversation_history(self) -> List[Dict]:
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]
    
    def get_recent_messages(self, count: int = 5) -> List[ConversationMessage]:
        return self.messages[-count:] if self.messages else []
    
    def get_conversation_summary(self) -> str:
    
        if not self.messages:
            return "No conversation yet."
        
        user_messages = [m for m in self.messages if m.role == "user"]
        assistant_messages = [m for m in self.messages if m.role == "assistant"]
        
        total_length = sum(len(m.content) for m in self.messages)
        avg_user_msg = (
            sum(len(m.content) for m in user_messages) / len(user_messages)
            if user_messages else 0
        )
        avg_assistant_msg = (
            sum(len(m.content) for m in assistant_messages) / len(assistant_messages)
            if assistant_messages else 0
        )
        
        return (
            f"Conversation Summary:\n"
            f"- User Messages: {len(user_messages)}\n"
            f"- Assistant Messages: {len(assistant_messages)}\n"
            f"- Total Characters: {total_length}\n"
            f"- Avg User Message: {avg_user_msg:.0f} chars\n"
            f"- Avg Assistant Message: {avg_assistant_msg:.0f} chars"
        )
    
    def optimize_memory(self):
        max_history = Config.MAX_CONVERSATION_HISTORY
        
        if len(self.messages) > max_history:
            removed = len(self.messages) - max_history
            self.messages = self.messages[-max_history:]
            self.logger.info(f"Optimized memory: removed {removed} old messages")
    
    def clear_history(self):

        self.messages = []
        self.session_start = datetime.now()
        self.logger.info("Conversation history cleared")
    
    def get_session_stats(self) -> Dict:

        user_messages = [m for m in self.messages if m.role == "user"]
        assistant_messages = [m for m in self.messages if m.role == "assistant"]
        
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "total_messages": len(self.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_characters": sum(len(m.content) for m in self.messages),
            "session_duration_seconds": session_duration,
            "session_start": self.session_start.isoformat()
        }
    
    def export_conversation(self) -> List[Dict]:

        return [msg.to_dict() for msg in self.messages]
    
    def display_conversation(self) -> str:

        if not self.messages:
            return "Conversation is empty."
        
        formatted = []
        for msg in self.messages:
            formatted.append(msg.get_formatted_text())
        
        return "\n".join(formatted)
    
    def get_context_window(self, max_tokens: int = 4000) -> Tuple[List[Dict], int]:

        
        estimated_tokens = 0
        context = []
        
        
        for msg in reversed(self.messages):
            msg_tokens = len(msg.content) 
            
            if estimated_tokens + msg_tokens > max_tokens:
                break
            
            context.insert(0, msg.to_dict())
            estimated_tokens += msg_tokens
        
        return context, estimated_tokens
