import inspect
from typing import Type, List

import telebot

import commands
from utils import DotEnvData
from processor import Command, DbData, Reaction

import logging

logging.basicConfig(level=logging.INFO, filename='logs.log', filemode='w', encoding='utf-8')

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
    try:
        command = command_define(message)
    
        db = DbData()
    
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

    except Exception as err:
        logging.error(err)


@bot.message_reaction_handler()
def reaction_handler(reaction: telebot.types.MessageReactionUpdated):
    try:
        react = Reaction(reaction)

        command = react.define()

        if not command:
            return

        new_message = command()

        if new_message:
            new_message.send()

    except Exception as err:
        logging.error(err)


@bot.edited_message_handler(content_types=['text', 'photo'])
def edited_handler(message: telebot.types.Message):
    try:
        db = DbData()
        if message.content_type == 'text':
            db.edit_message(message.message_id, message.text)
        elif message.content_type == 'photo':
            db.edit_message(message.message_id, message.caption, message.json['photo'][-1]['file_id'])
    except Exception as err:
        logging.error(err)


if __name__ == '__main__':
    DbData().first_launch()
    while True:
        try:
            bot.infinity_polling(timeout=10000, allowed_updates=['message', 'message_reaction', 'edited_message'])
        except:
            continue