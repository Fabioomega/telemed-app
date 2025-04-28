import ollama
from ollama import AsyncClient
from typing import NamedTuple


class Block(NamedTuple):
    start: str
    end: str


class LLM:

    def __init__(
        self,
        host: str,
        prompt: str,
        model: str,
        image_token: str,
        base_template: str,
        user_template: Block,
        assistant_template: Block,
    ):
        self.client = AsyncClient(host)
        self.prompt = prompt
        self.model = model
        self.image_token = image_token
        self.base_template = base_template
        self.user_template = user_template
        self.assistant_template = assistant_template

    def _format_prompt_unfinished_prompt(self, user_prompt: str, assistant_text: str):
        return f"{self.base_template}{self.user_template.start}{self.image_token}{user_prompt}{self.user_template.end}{self.assistant_template.start}{assistant_text}"

    async def complete(self, assistant_start: str, image: str) -> str:
        output = await self.client.generate(
            self.model,
            self._format_prompt_unfinished_prompt(self.prompt, assistant_start),
            raw=True,
            images=[image],
        )
        return assistant_start + output.response

    # except ollama.ResponseError:
    #     return "The analysis server seems to be offline!"

    async def generate(self, image: str) -> str:

        output = await self.client.generate(self.model, self.prompt, images=[image])
        return output.response

    # except ollama.ResponseError:
    #     return "The analysis server seems to be offline!"
