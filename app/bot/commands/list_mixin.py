from typing import Type

from app.bot.commands.base import CommandInterface


class CommandListMixin:
    commands = {}

    @classmethod
    def add(cls, command: CommandInterface):
        cls.commands[command.name] = command


def command_list(cls: Type[CommandInterface]):
    CommandListMixin.add(cls())
    return cls
