import json
import os
from abc import ABC, abstractmethod
import sqlite3
from typing import Type
from string import Template

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
        db.add_message(sent_message)

        return sent_message

    def delete_message(self, chat_id, message_id):
        try:
            self.bot.delete_message(chat_id, message_id)
        except Exception as err:
            print(f'\033[31mERROR:\033[0m {err.__str__()}')


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
            from main import bot
            me = bot.get_me()
            self.execute("""
                        INSERT INTO user 
                        (user_id, first_name, username) 
                        VALUES (?, ?, ?);
                    """, (me.id, me.first_name, me.username))

    def execute(self, query: str, parameters: tuple = (), fetch: str = 'one'):
        try:
            cursor = self.connect.cursor()
            cursor.execute('BEGIN')
            cursor.execute(query, parameters)
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'many':
                result = cursor.fetchmany()
            else:
                raise Exception('Need to use one of this fetch: one, all, many')
            self.connect.commit()
            return result
        except sqlite3.IntegrityError as err:
            if err.__str__() not in ('UNIQUE constraint failed: chat.chat_id, chat.topic',
                                     'UNIQUE constraint failed: user.user_id',):
                print(f'\033[31mERROR:\033[0m {err.__str__()}')
                return None
            self.connect.rollback()
            return f'\033[31mERROR:\033[0m {err.__str__()}'

    def add_message(self, message: telebot.types.Message):
        message_id = message.message_id
        chat_id = message.chat.id
        user_id = message.from_user.id
        text = message.text
        topic = None
        reply_to_message_id = None

        is_topic = message.is_topic_message

        if is_topic:
            topic = message.message_thread_id
            if not message.reply_to_message.content_type == 'forum_topic_created':
                reply_to_message_id = message.reply_to_message.message_id
        else:
            topic = None
            if reply_to_message_id:
                reply_to_message_id = message.reply_to_message.message_id

        if not topic:
            topic = 0

        self.execute("""
            INSERT INTO message 
            (message_id, chat, user, text, reply_to_message_id)
            VALUES 
            (?, (SELECT id FROM chat WHERE chat_id = ? and topic = ?), (SELECT id FROM user WHERE user_id = ?), ?, ?);
        """, (message_id, chat_id, topic, user_id, text, reply_to_message_id))

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

    def set_emoji(self, emoji: str, chat_id: int, topic: str) -> None:
        res = self.execute("""
            UPDATE chat SET emoji = ? WHERE chat_id = ? and topic = ?;
        """, (emoji, chat_id, topic))


class Command(ABC):
    def __init__(self, message: telebot.types.Message):
        self.message = message
        self.text = message.text
        self.text_low = message.text.lower()
        self.chat_id = message.chat.id
        self.chat_type = message.chat.type
        self.topic = message.message_thread_id
        if not self.topic:
            self.topic = 0

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


class Reaction:
    def __init__(self, reaction: telebot.types.MessageReactionUpdated):
        self.reaction = reaction
        self.db = DbData()
        self.locales_data = LocalesData().data

        self.old_emoji = None
        self.new_emoji = None

        if self.reaction.old_reaction:
            self.old_emoji = reaction.old_reaction[0].to_dict()['emoji']
        if self.reaction.new_reaction:
            self.new_emoji = reaction.new_reaction[0].to_dict()['emoji']

        self.message_id = reaction.message_id
        self.chat_id = reaction.chat.id
        self.user_id = reaction.user.id
        self.topic = None
        self._define_topic()

    def _define_topic(self) -> None:
        res = self.db.execute("""
            SELECT chat.topic 
            FROM message 
            INNER JOIN chat 
            ON message.chat = chat.id 
            WHERE message.message_id = ?;
        """, (self.message_id, ))
        print(self.message_id)
        print(self.chat_id)
        print(res)
        if res:
            self.topic = res[0]
            return
        else:
            print('Topic not define, wtf')
        return self.register_error_message('message_created_before_bot_connected')

    def define(self):
        if self.old_emoji and not self.new_emoji:
            return None

        # Проверка наличия темы текущего чата с данным emoji
        res1 = self.db.execute("""
                     SELECT * FROM chat WHERE chat_id = ? and emoji = ?;
                 """, (self.chat_id, self.new_emoji))

        if res1:
            return self.resend_message
        else:
            res2 = self.db.execute("""
                    SELECT emoji FROM chat WHERE chat_id = ? and topic = ?;
                """, (self.chat_id, self.topic))
            if res2:
                if res2[0].isnumeric():
                    return self.register_topic
                else:
                    return None
            else:
                return None

    def register_topic(self) -> MessageToSend:

        self.db.set_emoji(self.new_emoji, self.chat_id, self.topic)

        new_message = MessageToSend()

        new_message.chat_id = self.chat_id
        new_message.text = Template(self.locales_data['register_topic']['ru']).substitute(emoji=self.new_emoji)
        new_message.thread = self.topic

        return new_message

    def resend_message(self) -> MessageToSend:
        topic = self.db.execute("""
            SELECT topic FROM chat WHERE chat_id = ? and emoji = ?;
        """, (self.chat_id, self.new_emoji))[0]

        find_text_res = self.db.execute("""
            SELECT text FROM message WHERE message_id = ?;
        """, (self.message_id, ))

        try:
            text = find_text_res[0]
        except:
            raise Exception("Какая-то ошибка")

        new_message = MessageToSend()

        new_message.chat_id = self.chat_id
        new_message.thread = topic
        new_message.text = text

        return new_message

    def register_error_message(self, error: str) -> None:
        if error == 'same_emoji_in_this_chat':
            new_message = MessageToSend()

            new_message.chat_id = self.chat_id
            new_message.thread = self.topic
            new_message.text = (Template(self.locales_data['same_emoji_in_this_chat']['ru'])
                                .substitute(emoji=self.new_emoji))

            new_message.send()
        elif error == 'message_created_before_bot_connected':
            new_message = MessageToSend()

            new_message.chat_id = self.chat_id
            new_message.thread = self.topic
            new_message.text = (Template(self.locales_data['message_created_before_bot_connected']['ru'])
                                .substitute(emoji=self.new_emoji))

            new_message.send()

