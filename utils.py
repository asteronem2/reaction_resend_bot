import os

from dotenv import load_dotenv


class DotEnvData:
    BOT_TOKEN = None
    ADMIN_LIST = None

    def __init__(self):
        load_dotenv('param.env')
        environ = os.environ
        self.BOT_TOKEN = environ.get('BOT_TOKEN')
        self.ADMIN_LIST = environ.get('ADMIN_LIST').split(' ')


