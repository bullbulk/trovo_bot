from langchain_ollama import ChatOllama

from app.trovo_bot.bot.trovo.schemas import Message
from loguru import logger
from app.utils.config import settings


class OllamaChatController(ChatOllama):
    def __init__(
        self,
        *args,
        base_url=str(settings.OLLAMA_HOST_URL),
        model=settings.OLLAMA_MODEL_NAME,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
            base_url=base_url,
            model=model,
        )

    async def handle_message(self, message: Message):
        llm_request = f"{message.nick_name}: {message.content}"
        llm_request = llm_request.replace("SYSTEM \"", "").replace("system \"", "")
        logger.info(f"LLM Request: {llm_request}")
        llm_response = await self.ainvoke([("human", llm_request)])
        logger.info(f"LLM Response: {llm_response}")
        return llm_response.content
