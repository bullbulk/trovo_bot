class CommandRegistry(type):
    commands = {}

    def __new__(cls, *args, **kwargs):
        class_ = super().__new__(cls, *args, **kwargs)

        name = getattr(class_, "name", None)
        aliases = getattr(class_, "aliases", None)

        if (
            name is None or aliases is None
        ):
            return class_


        if not (name or aliases):
            raise ValueError("Command should have name or aliases set")

        aliases = aliases or []

        for alias in [name, *aliases]:
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
