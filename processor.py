import json
import os
import time
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
    reply_to_message_id = None
    media_id = None
    message_id: int

    def send(self) -> telebot.types.Message:
        if not self.media_id:
            sent_message = self.bot.send_message(chat_id=self.chat_id,
                                                 text=self.text,
                                                 message_thread_id=self.thread,
                                                 reply_markup=self.markup,
                                                 parse_mode='html',
                                                 reply_to_message_id=self.reply_to_message_id,
                                                 disable_notification=True,
                                                 )
        else:
            sent_message = self.bot.send_photo(chat_id=self.chat_id,
                                               photo=self.media_id,
                                               caption=self.text,
                                               message_thread_id=self.thread,
                                               reply_markup=self.markup,
                                               parse_mode='html',
                                               reply_to_message_id=self.reply_to_message_id,
                                               disable_notification=True,
                                               )

        db = DbData()
        db.add_message(sent_message)

        return sent_message

    def delete_message(self):
        try:
            self.bot.delete_message(self.chat_id, self.message_id)
        except Exception as err:
            print(f'\033[31mERROR:\033[0m {err.__str__()}')

    def edit_message(self):
        try:

            dots = '.'
            for i in range(4):
                self.bot.edit_message_text(text=f'Изменяем{dots}',
                                           chat_id=self.chat_id,
                                           message_id=self.message_id,
                                           )
                if dots == '.':
                    dots = '..'
                elif dots == '..':
                    dots = '...'
                elif dots == '...':
                    dots = '.'
                time.sleep(0.25)

            self.bot.edit_message_text(text=self.text,
                                       chat_id=self.chat_id,
                                       message_id=self.message_id
                                       )
        except Exception as err:
            print(f'\033[31mERROR:\033[0m {err.__str__()}')

    def edit_photo(self):
        try:

            dots = '.'
            for i in range(4):
                photo_object = telebot.types.InputMediaPhoto(
                    media=self.media_id,
                    caption=f'Изменяем{dots}',
                    parse_mode='html',
                )

                self.bot.edit_message_media(media=photo_object,
                                            chat_id=self.chat_id,
                                            message_id=self.message_id
                                            )
                if dots == '.':
                    dots = '..'
                elif dots == '..':
                    dots = '...'
                elif dots == '...':
                    dots = '.'
                time.sleep(0.25)

            photo_object = telebot.types.InputMediaPhoto(
                media=self.media_id,
                caption=self.text,
                parse_mode='html',
            )

            self.bot.edit_message_media(media=photo_object,
                                        chat_id=self.chat_id,
                                        message_id=self.message_id
                                        )

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
        content_type = message.content_type
        media_id = None
        text = None
        topic = None
        reply_to_message_id = None
        quote_start = None
        quote_end = None

        if message.quote:
            quote_start = message.quote.position
            text_len = len(message.quote.text)
            quote_end = quote_start + text_len

        if content_type == 'text':
            text = message.text
        elif content_type == 'photo':
            text = message.caption
            media_id = message.json['photo'][-1]['file_id']

        is_topic = message.is_topic_message

        if is_topic:
            topic = message.message_thread_id
            if not message.reply_to_message.content_type == 'forum_topic_created':
                reply_to_message_id = message.reply_to_message.message_id
        else:
            topic = None
            if message.reply_to_message:
                reply_to_message_id = message.reply_to_message.message_id

        if not topic:
            topic = 0

        self.execute("""
            INSERT INTO message 
            (message_id, chat, user, text, reply_to_message_id, media_id, content_type, quote_start, quote_end)
            VALUES 
            (?, (SELECT id FROM chat WHERE chat_id = ? and topic = ?), (SELECT id FROM user WHERE user_id = ?), ?, ?, ?, 
            ?, ?, ?);
        """, (message_id, chat_id, topic, user_id, text, reply_to_message_id, media_id, content_type, quote_start,
              quote_end))

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
        self.execute("""
            UPDATE chat SET emoji = ? WHERE chat_id = ? and topic = ?;
        """, (emoji, chat_id, topic))

    def set_emoji_to_edit(self, emoji: str, chat_id: int, topic: str) -> None:
        self.execute("""
            UPDATE chat SET emoji_to_edit = ? WHERE chat_id = ? and topic = ?;
        """, (emoji, chat_id, topic))


class Command(ABC):
    def __init__(self, message: telebot.types.Message):
        self.message = message
        self.text = message.text
        if self.text:
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
        self.content_type_message = None
        self._check_content_type_message()
        self.topic = None
        self._define_topic()

    def _check_content_type_message(self):
        res = self.db.execute("""
            SELECT content_type FROM message WHERE message_id = ?;
        """, (self.message_id,))
        self.content_type_message = res[0]

    def _define_topic(self) -> None:
        res = self.db.execute("""
            SELECT chat.topic 
            FROM message 
            INNER JOIN chat 
            ON message.chat = chat.id 
            WHERE message.message_id = ?;
        """, (self.message_id,))
        if res:
            self.topic = res[0]
            return
        else:
            print('Topic not define, wtf')
        return self.register_error_message('message_created_before_bot_connected')

    def define(self):
        from main import EnvData

        if self.reaction.user.username not in EnvData.ADMIN_LISt:
            return None

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
                    if int(res2[0]) == self.message_id:
                        return self.register_emoji

        res3 = self.db.execute("""
                     SELECT emoji_to_edit FROM chat WHERE chat_id = ? and topic = ?;
                 """, (self.chat_id, self.topic))

        if res3 and res3[0]:
            if res3[0].isnumeric():
                if int(res3[0]) == self.message_id:
                    return self.register_emoji_to_edit
            elif res3[0] == self.new_emoji:
                res4 = self.db.execute("""
                    SELECT reply_to_message_id FROM message WHERE message_id = ?;
                """, (self.message_id,))

                if res4[0]:
                    res5 = self.db.execute("""
                         SELECT user FROM message WHERE message_id = ?;
                    """, (res4[0],))
                    if res5[0] == 1:
                        return self.edit_message

        return None

    def register_emoji(self) -> MessageToSend:

        res = self.db.execute("""
            SELECT * FROM chat WHERE emoji_to_edit = ?;
        """, (self.new_emoji,))
        res2 = self.db.execute("""
            SELECT * FROM chat WHERE emoji = ?;
        """, (self.new_emoji,))

        if res or res2:
            self.register_error_message('emoji_already_taker')
            return None

        self.db.set_emoji(self.new_emoji, self.chat_id, self.topic)

        new_message = MessageToSend()

        new_message.chat_id = self.chat_id
        new_message.text = Template(self.locales_data['register_topic']['ru']).substitute(emoji=self.new_emoji)
        new_message.thread = self.topic

        return new_message

    def register_emoji_to_edit(self) -> MessageToSend:

        res = self.db.execute("""
            SELECT * FROM chat WHERE emoji_to_edit = ?;
        """, (self.new_emoji,))
        res2 = self.db.execute("""
            SELECT * FROM chat WHERE emoji = ?;
        """, (self.new_emoji,))

        if res or res2:
            self.register_error_message('emoji_already_taker')
            return None

        self.db.set_emoji_to_edit(self.new_emoji, self.chat_id, self.topic)

        new_message = MessageToSend()

        new_message.chat_id = self.chat_id
        new_message.text = Template(self.locales_data['register_emoji_to_edit']['ru']).substitute(emoji=self.new_emoji)
        new_message.thread = self.topic

        return new_message

    def resend_message(self) -> MessageToSend:
        topic = self.db.execute("""
            SELECT topic FROM chat WHERE chat_id = ? and emoji = ?;
        """, (self.chat_id, self.new_emoji))[0]

        find_text_res = self.db.execute("""
            SELECT text, media_id FROM message WHERE message_id = ?;
        """, (self.message_id,))

        try:
            text, media_id = find_text_res
        except:
            raise Exception("Какая-то ошибка")

        reply_to_message_id = None

        res = self.db.execute("""
            SELECT reply_to_message_id FROM message WHERE message_id = ?;
        """, (self.message_id,))

        if type(res[0]) is int:
            reply_to_message_id = self._send_chain_message(res[0], topic)

        deleted_message = MessageToSend()

        deleted_message.chat_id = self.chat_id
        deleted_message.message_id = self.message_id

        deleted_message.delete_message()

        new_message = MessageToSend()

        new_message.chat_id = self.chat_id
        new_message.thread = topic
        new_message.reply_to_message_id = reply_to_message_id
        new_message.text = text
        new_message.media_id = media_id

        return new_message

    def edit_message(self) -> None:
        print("EDIT MESSAGE")
        res1 = self.db.execute("""
            SELECT reply_to_message_id, text, quote_start, quote_end, media_id FROM message WHERE message_id = ?; 
        """, (self.message_id,))
        message_to_edit_id = res1[0]
        text_to_edit = res1[1]
        quote_start = res1[2]
        quote_end = res1[3]

        res2 = self.db.execute("""
            SELECT text, media_id FROM message WHERE message_id = ?;
        """, (res1[0],))

        if quote_start:
            initial_text = res2[0]
            first_part_text = initial_text[:quote_start]
            second_part_text = text_to_edit
            third_part_text = initial_text[quote_end:]

            text_to_edit = first_part_text + second_part_text + third_part_text

        deleted_message = MessageToSend()
        deleted_message.message_id = self.message_id
        deleted_message.chat_id = self.chat_id

        # Если редактируемое сообщение с фото
        if res2[1]:
            if res1[4]:
                # Если редактирующее сообщение с фото и текстом
                if res1[1]:
                    edited_photo = MessageToSend()

                    edited_photo.media_id = res1[4]
                    edited_photo.text = text_to_edit
                    edited_photo.chat_id = self.chat_id
                    edited_photo.message_id = message_to_edit_id

                    edited_photo.edit_photo()
                    deleted_message.delete_message()
                    return None

                # Если редактирующее сообщение с фото и без текста
                else:
                    edited_photo = MessageToSend()

                    edited_photo.media_id = res1[4]
                    edited_photo.text = res2[0]
                    edited_photo.chat_id = self.chat_id
                    edited_photo.message_id = message_to_edit_id

                    edited_photo.edit_photo()
                    deleted_message.delete_message()
                    return None

            # Если редактирующее сообщение без фото
            else:
                edited_photo = MessageToSend()

                edited_photo.media_id = res2[1]
                edited_photo.text = text_to_edit
                edited_photo.chat_id = self.chat_id
                edited_photo.message_id = message_to_edit_id

                edited_photo.edit_photo()
                deleted_message.delete_message()
                return None

        edited_message = MessageToSend()
        edited_message.chat_id = self.chat_id
        edited_message.text = text_to_edit
        edited_message.message_id = message_to_edit_id

        edited_message.edit_message()
        deleted_message.delete_message()

        return None

    def register_error_message(self, error: str) -> None:
        if error == 'emoji_already_taker':
            new_message = MessageToSend()

            new_message.chat_id = self.chat_id
            new_message.thread = self.topic
            new_message.text = '<b>Данный эмодзи уже занят</b>'

            new_message.send()
        else:
            new_message = MessageToSend()

            new_message.chat_id = self.chat_id
            new_message.thread = self.topic
            new_message.text = '<b>Ошибка какая-то</b>'

            new_message.send()

    def _send_chain_message(self, first_replied: int, topic) -> int:
        chain_of_message = []

        replied_id = first_replied

        while replied_id:
            res = self.db.execute("""
                SELECT reply_to_message_id, message_id, text, media_id FROM message WHERE message_id = ?;
            """, (replied_id,))

            replied_id = res[0]
            if res:
                chain_of_message.append(res)

        chain_of_message = chain_of_message[::-1]

        reply_to_message_id = None

        for message_info in chain_of_message:
            deleted_message = MessageToSend()
            deleted_message.message_id = message_info[1]
            deleted_message.chat_id = self.chat_id
            deleted_message.delete_message()

            new_message = MessageToSend()

            new_message.reply_to_message_id = reply_to_message_id
            new_message.text = message_info[2]
            new_message.media_id = message_info[3]
            new_message.thread = topic
            new_message.chat_id = self.chat_id

            res = new_message.send()
            reply_to_message_id = res.message_id

            time.sleep(0.5)

        return reply_to_message_id
