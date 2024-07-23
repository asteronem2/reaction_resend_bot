import telebot.types
from abc import ABC, abstractmethod


class MessageToSend:
    text: str
    chat_id: str
    thread: int

    def send(self):
        pass


class Command(ABC):
    def __init__(self, message: telebot.types.Message):
        self.message = message
        self.text = message.text
        self.text_low = message.text.lower()
        self.chat_id = message.chat.id
        self.chat_type = message.chat.type

    @abstractmethod
    def define(self) -> bool:
        pass

    @abstractmethod
    def new_message_generate(self) -> MessageToSend:
        pass


class Message:
    command_texts = {
        'c_start': '/start',
        'c_topic': '/topic',
    }

    command = None

    def __init__(self, message: telebot.types.Message) -> None:
        self.message = message
        self._command_define()

    def _command_define(self) -> None:
        for command, keyword in self.command_texts.items():
            if self.message.text == keyword:
                self.command = command
                return

