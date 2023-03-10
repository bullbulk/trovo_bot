from .base import CommandInstance


class CommandListController:
    commands: dict[str, CommandInstance] = {}

    @classmethod
    def add(cls, command: CommandInstance):
        cls.commands[command.name] = command


def get_commands() -> dict[str, CommandInstance]:
    return {x: y for x, y in CommandListController.commands.items() if not y.disabled}
