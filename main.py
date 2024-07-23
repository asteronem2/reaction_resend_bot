import inspect
import os
from typing import Type, List

import telebot

import commands
from utils import DotEnvData
from processor import Command


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
def message_handler(message):
    command = command_define(message)

    if not command:
        return

    new_message = command.new_message_generate()
    new_message.send()


@bot.message_reaction_handler()
def reaction_handler(reaction):
    print(type(reaction))
    print(reaction.new_reaction)
    telebot.types.ReactionTypeEmoji


if __name__ == '__main__':
    bot.infinity_polling(timeout=100, allowed_updates=['message', 'message_reaction'])

