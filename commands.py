from string import Template

import telebot

from processor import Command, MessageToSend


class CommandStart(Command):
    def define(self) -> bool:
        if self.text_low == '/start' and self.chat_type == 'private':
            return True
        else:
            return False

    def new_message_generate(self) -> MessageToSend:
        new_message = MessageToSend()

        new_message.text = (Template(self.locales_data['/start']['ru'])
                            .substitute(name=self.message.from_user.first_name))
        new_message.thread = self.message.message_thread_id
        new_message.chat_id = self.message.chat.id

        return new_message

    def processing(self, sent_message: telebot.types.Message) -> None:
        # res = self.db.execute('')
        pass


class CommandTopic(Command):
    def define(self) -> bool:
        if self.text_low == '/topic' and self.chat_type == 'supergroup':
            return True
        else:
            return False

    def new_message_generate(self) -> MessageToSend:
        new_message = MessageToSend()

        new_message.text = (Template(self.locales_data['/topic']['ru'])
                            .substitute(name=self.message.from_user.first_name))
        new_message.thread = self.message.message_thread_id
        new_message.chat_id = self.message.chat.id

        # Добавление информации о прошлом эмодзи, если оно было
        res = self.db.execute("""
            SELECT emoji FROM chat WHERE chat_id = ? and topic = ?;
        """, (self.chat_id, self.topic))

        if res and type(res) is tuple:
            if res[0] and not res[0].isnumeric():
                new_message.text += f'\n<i>Предыдущий эмодзи:</i> {res[0]}'

        return new_message

    def processing(self, sent_message: telebot.types.Message) -> None:

        res = self.db.execute("""
            SELECT emoji FROM chat WHERE chat_id = ? and topic = ?;
        """, (self.chat_id, self.topic))

        if type(res) is tuple:
            self.db.set_emoji(str(sent_message.message_id), self.chat_id, self.topic)
        else:
            raise Exception('Нет значения с таким chat_id и topic')


class CommandLang(Command):
    def define(self) -> bool:
        if self.text_low == '/lang' and self.chat_type == 'private':
            return True
        else:
            return False

    def new_message_generate(self) -> MessageToSend:
        new_message = MessageToSend()

        new_message.text = Template(self.locales_data['/lang']['ru']).substitute()
        new_message.thread = self.message.message_thread_id
        new_message.chat_id = self.message.chat.id

        return new_message

    def processing(self, sent_message: telebot.types.Message) -> None:
        pass
