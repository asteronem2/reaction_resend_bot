import telebot

from utils import DotEnvData
from processor import Message, SendMessage


EnvData = DotEnvData()

bot = telebot.TeleBot(token=EnvData.BOT_TOKEN)


@bot.message_handler()
def message_handler(message):
    print(type(message))
    return
    msg = Message(message)

    if not msg.command:
        return


    new_message = SendMessage()



@bot.message_reaction_handler()
def reaction_handler(reaction):
    print(reaction)


if __name__ == '__main__':
    bot.infinity_polling(timeout=100, allowed_updates=['message', 'message_reaction'])
