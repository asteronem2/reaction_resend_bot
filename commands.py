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

        new_message.text = Template(self.locales_data['/start']['ru']).substitute(name=self.message.from_user.first_name)
        new_message.thread = self.message.message_thread_id
        new_message.chat_id = self.message.chat.id

        return new_message

    def processing(self, sent_message: telebot.types.Message) -> None:
        # res = self.db.execute('')
        pass

class CommandTopic(Command):
    def define(self) -> bool:
        if self.text_low == '/topic':
            return True
        else:
            return False

    def new_message_generate(self) -> MessageToSend:
        new_message = MessageToSend()

        new_message.text = Template(self.locales_data['/start']['ru']).substitute(name=self.message.from_user.first_name)
        new_message.thread = self.message.message_thread_id
        new_message.chat_id = self.message.chat.id

        return new_message

    def processing(self, sent_message: telebot.types.Message) -> None:
        pass

class CommandLang(Command):
    def define(self) -> bool:
        if self.text_low == '/lang' and self.chat_type == 'private':
            return True
        else:
            return False

    def new_message_generate(self) -> MessageToSend:
        new_message = MessageToSend()

        new_message.text = Template(self.locales_data['/lang']['ru'])
        new_message.thread = self.message.message_thread_id
        new_message.chat_id = self.message.chat.id

        return new_message

    def processing(self, sent_message: telebot.types.Message) -> None:
        pass

