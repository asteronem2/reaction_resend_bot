import inspect
import os
import time
from typing import Type, List

import telebot

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


@bot.message_handler()
def message_handler(message: telebot.types.Message):
    command = command_define(message)

    db = DbData()
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

    # new_message.send()


if __name__ == '__main__':
    bot.infinity_polling(timeout=100, allowed_updates=['message', 'message_reaction'])

