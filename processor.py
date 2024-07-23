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

    def send(self) -> telebot.types.Message:
        sent_message = self.bot.send_message(chat_id=self.chat_id,
                                             text=self.text,
                                             message_thread_id=self.thread,
                                             reply_markup=self.markup,
                                             parse_mode='html',
                                             )

        db = DbData()
        db.add_bot_message(sent_message)

        return sent_message


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

    def execute(self, query: str, parameters: tuple = ()):
        try:
            cursor = self.connect.cursor()
            cursor.execute('BEGIN')
            cursor.execute(query, parameters)
            result = cursor.fetchall()
            self.connect.commit()
            return result
        except sqlite3.IntegrityError as err:
            self.connect.rollback()
            return f'\033[31mERROR:\033[0m {err.__str__()}'

    def add_bot_message(self, message: telebot.types.Message):
        self.execute("""
            INSERT INTO bot_message 
            (message_id, chat_id, text)
            VALUES 
            (?, (SELECT id FROM chat WHERE chat_id = ?), ?);
        """, (message.message_id, message.chat.id, message.text))

    def add_chat(self, message: telebot.types.Message):
        chat_id = message.chat.id
        topic = message.message_thread_id

        if not topic:
            topic = 0

        res = self.execute("""
            INSERT INTO chat 
            (chat_id, topic) 
            VALUES (?, ?);
        """, (chat_id, topic))

        if not res:
            print(f'\033[32mAdd new chat (\033[1;36m{chat_id}, {topic}\033[32m)\033[0m')

    def add_user(self, message: telebot.types.Message):
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username

        res = self.execute("""
            INSERT INTO user 
            (user_id, first_name, username) 
            VALUES (?, ?, ?);
        """, (user_id, first_name, username))

        if not res:
            print(f'\033[32mAdd new user (\033[1;36m{user_id}, {username}\033[32m)\033[0m')



class Command(ABC):
    def __init__(self, message: telebot.types.Message):
        self.message = message
        self.text = message.text
        self.text_low = message.text.lower()
        self.chat_id = message.chat.id
        self.chat_type = message.chat.type

        self.locales_data = LocalesData().data

        self.db = DbData()

    @abstractmethod
    def define(self) -> bool:
        pass

    @abstractmethod
    def new_message_generate(self) -> MessageToSend:
        pass

    @abstractmethod
    def processing(self, sent_message: telebot.types.Message) -> None:
        pass
