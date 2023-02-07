from .list_controller import CommandListController


def as_command(cls):
    CommandListController.add(cls())
    return cls
