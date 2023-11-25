from dataclasses import dataclass
from datetime import datetime

from models import ChatHistory


@dataclass
class DTOMessage:
    content: str
    update_time: str
    sender: str

    def __init__(self, chat_history: ChatHistory):
        self.content = chat_history.message
        self.update_time = str(chat_history.update_time)
        self.sender = "robot" if chat_history.is_robot else "user"


@dataclass
class DTOConversationMessage:
    conversation_id: int
    message_list: list[DTOMessage]

    def __init__(self, conversation_id: int):
        self.conversation_id = conversation_id
        self.message_list = []

    def __init__(self, conversation_id: int):
        self.conversation_id = conversation_id
        self.message_list = []