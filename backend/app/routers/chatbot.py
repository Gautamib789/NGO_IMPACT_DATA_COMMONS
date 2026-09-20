from pydantic import BaseModel
from fastapi import APIRouter
from app.services.ai_chatbot import AIChatbotService

router = APIRouter(prefix="/api/chat", tags=["AI Transparency Assistant"])


class ChatQuery(BaseModel):
    message: str


@router.post("")
def chat_with_assistant(query: ChatQuery):
    response = AIChatbotService.get_response(query.message)
    return {"message": query.message, "response": response}
