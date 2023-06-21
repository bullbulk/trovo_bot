from .base import Command


class CommandRegistry(type):
    commands: dict[str, Command] = {}

    def __new__(cls, *args, **kwargs):
        class_ = super().__new__(cls, *args, **kwargs)

        name = getattr(class_, "name")
        aliases = getattr(class_, "aliases")

        if not (name or aliases):
            raise ValueError("Command should have name or aliases set")

        aliases = aliases or []
        if name:
            aliases.insert(0, name)

        for alias in aliases:
            cls.commands[alias] = class_()

        return class_

    @classmethod
    def add(cls, command: Command):
        cls.commands[command.name] = command

    @classmethod
    def get(cls, name: str):
        return cls.commands.get(name)

    @classmethod
    def get_commands(cls) -> dict[str, Command]:
        return {x: y for x, y in cls.commands.items() if not y.disabled}
