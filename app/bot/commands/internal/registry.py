class CommandRegistry(type):
    commands = {}

    def __new__(cls, *args, **kwargs):
        class_ = super().__new__(cls, *args, **kwargs)

        if not (hasattr(class_, "name") or hasattr(class_, "aliases")):
            return class_

        name = getattr(class_, "name", None)
        aliases = getattr(class_, "aliases", None)

        if not (name or aliases):
            raise ValueError("Command should have name or aliases set")

        aliases = aliases or []
        if name:
            aliases.insert(0, name)

        for alias in aliases:
            cls.commands[alias] = class_()

        return class_

    @classmethod
    def add(cls, command):
        cls.commands[command.name] = command

    @classmethod
    def get(cls, name: str):
        return cls.commands.get(name)

    @classmethod
    def get_commands(cls):
        return {x: y for x, y in cls.commands.items() if not y.disabled}
