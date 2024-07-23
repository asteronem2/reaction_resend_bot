from processor import Command, MessageToSend


class CommandStart(Command):
    def define(self) -> bool:
        if self.text_low == '/start':
            return True
        else:
            return False

    def new_message_generate(self) -> MessageToSend:
        pass


class CommandTopic(Command):
    pass
