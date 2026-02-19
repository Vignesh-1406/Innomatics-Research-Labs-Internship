import google.generativeai as genai
import traceback
from config import Config
from utils.logger import ChatbotLogger
from prompts import SystemPrompt


class GeminiService:

    def __init__(self):
        self.logger = ChatbotLogger.get_logger(__name__)
        self.api_key = Config.GEMINI_API_KEY
        self.temperature = Config.TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS

        if not self.api_key:
            error_msg = "GEMINI_API_KEY is not configured in environment variables"
            self.logger.error(f"GeminiServiceError: {error_msg}")
            raise ValueError(error_msg)

        genai.configure(api_key=self.api_key)
        self.logger.info("Gemini API configured successfully with model: gemini-2.5-flash")

    def send_message(
        self,
        conversation_history: list[dict],
        system_prompt: str | None = None
    ) -> str | None:

        try:
            if system_prompt is None:
                system_prompt = SystemPrompt.get_system_prompt()

            model = genai.GenerativeModel("gemini-2.5-flash")

            formatted_history = []

            if conversation_history:
                for msg in conversation_history[:-1]:
                    formatted_history.append({
                        "role": "user" if msg["role"] == "user" else "model",
                        "parts": [msg["content"]]
                    })

            chat = model.start_chat(history=formatted_history)

            last_message = conversation_history[-1]["content"] if conversation_history else ""

            if not formatted_history:
                last_message = f"{system_prompt}\n\n{last_message}"

            response = chat.send_message(
                last_message,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4096,
                    temperature=0.7
                )
            )

            response_text = response.text

            if not response_text:
                self.logger.warning("Received empty response from Gemini API")
                return None

            self.logger.info("Successfully generated response from gemini-2.5-flash")

            return response_text

        except Exception as e:
            error_msg = f"Error communicating with Gemini API: {str(e)}"
            self.logger.error(f"GeminiError: {error_msg}\n{traceback.format_exc()}")

            return self._get_fallback_response(
                "api_error",
                "I'm experiencing technical difficulties connecting to the AI service. Please try again in a moment."
            )

    def _get_fallback_response(self, error_type: str, message: str) -> str:
        self.logger.warning(f"Returning fallback response for {error_type}")
        return (
            f"{message}\n\n"
            "In the meantime, consider:\n"
            "- Reviewing your career goals and skills\n"
            "- Preparing questions about your career path\n"
            "- Researching industry trends in your field"
        )

    def validate_response(self, response: str) -> bool:
        if not response or not isinstance(response, str):
            return False
        if len(response.strip()) < 10:
            return False
        return True

    def get_model_info(self) -> dict:
        return {
            "model": "gemini-2.5-flash",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "configured": self.api_key is not None
        }

    @staticmethod
    def test_connection() -> bool:
        try:
            logger = ChatbotLogger.get_logger(__name__)
            service = GeminiService()

            test_response = service.send_message(
                [{"role": "user", "content": "Say hello"}],
                system_prompt="Respond with a simple greeting."
            )

            if test_response:
                logger.info("Gemini API connection test successful")
                return True
            else:
                logger.error("Gemini API connection test failed: empty response")
                return False

        except Exception as e:
            logger = ChatbotLogger.get_logger(__name__)
            logger.error(f"Gemini API connection test failed: {str(e)}")
            return False
