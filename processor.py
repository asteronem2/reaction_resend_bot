import json
import os
from abc import ABC, abstractmethod
import sqlite3

import telebot.types


class MessageToSend:
    def __init__(self):
        from main import bot
        self.bot = bot

    text: str
    chat_id: str
    thread: int
    markup: telebot.types.InlineKeyboardMarkup = None

    def send(self):
        self.bot.send_message(chat_id=self.chat_id,
                              text=self.text,
                              message_thread_id=self.thread,
                              reply_markup=self.markup,
                              parse_mode='html',
                              )


class LocalesData:
    _filename = 'locales.json'

    def __init__(self):
        with open(self._filename, 'r') as readfile:
            data = json.load(readfile)
        self.data = data


class DbData:
    _dbname = 'data.db'
    _schema = 'schema.sql'

    def __init__(self):
        if os.path.exists(self._dbname):
            self.connect = sqlite3.connect(self._dbname)
        else:
            self.connect = sqlite3.connect(self._dbname)
            with open(self._schema, 'r') as readfile:
                schema = readfile.read()
            self.connect.executescript(schema)


class Command(ABC):
    def __init__(self, message: telebot.types.Message):
        self.message = message
        self.text = message.text
        self.text_low = message.text.lower()
        self.chat_id = message.chat.id
        self.chat_type = message.chat.type

        self.locales_data = LocalesData().data

    @abstractmethod
    def define(self) -> bool:
        pass

    @abstractmethod
    def new_message_generate(self) -> MessageToSend:
        pass
