import inspect
import os
import time
from typing import Type, List

import telebot
from telebot.types import InputMediaPhoto

import commands
import reactions
from utils import DotEnvData
from processor import Command, DbData, Reaction

EnvData = DotEnvData()

bot = telebot.TeleBot(token=EnvData.BOT_TOKEN)

all_command_cls: List[Type[Command]] = [i[1] for i in inspect.getmembers(commands, inspect.isclass)
                                        if i[1].__dict__['__module__'] == 'commands']


def command_define(message) -> Command:
    for cls in all_command_cls:
        instance = cls(message)
        if instance.define():
            return instance


@bot.message_handler(content_types=['text', 'photo'])
def message_handler(message: telebot.types.Message):
    command = command_define(message)

    db = DbData()

    # Если в чате есть несколько тем, reply_message и message_thread_id переплетаются
    # Если тема генеральная и сообщение обычное reply_message = None, message_thread_id = None
    # Если тема генеральная и сообщение replied, reply_message.message_id = replied-message_id, message_thread_id = replied-message_id
    # Если тема topic и сообщение обычыное reply_message.content_type = "forum_topic_created", reply_message.message_id = topic-create-message_id, message_thread_id = message_thread_id
    # Если тема topic и сообщение replied, reply_message.content_type = "text", reply_message.message_id = replied-message_id, message_thread_id = message_thread_id

    if message.reply_to_message:
        if message.reply_to_message.content_type == 'forum_topic_created':
            db.add_chat(message)
    else:
        db.add_chat(message)

    db.add_user(message)
    db.add_message(message)

    if not command:
        return

    new_message = command.new_message_generate()

    sent_message = new_message.send()

    command.processing(sent_message)


@bot.message_reaction_handler()
def reaction_handler(reaction: telebot.types.MessageReactionUpdated):
    react = Reaction(reaction)

    command = react.define()

    if not command:
        return

    new_message = command()

    if new_message:
        new_message.send()


if __name__ == '__main__':
    bot.infinity_polling(timeout=100, allowed_updates=['message', 'message_reaction'])
