from app.bot.api import Api


class SingletonRegistry:
    api: Api

    @classmethod
    def set_api(cls, api: Api):
        cls.api = api
