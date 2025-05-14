import base64
from ollama import AsyncClient
from openai import AsyncClient as OAsyncClient
from typing import NamedTuple
from PIL import Image
from io import BytesIO


class Block(NamedTuple):
    start: str
    end: str


def bytes_to_PIL(raw_img):
    return Image.open(BytesIO(raw_img))


def PIL_to_jpeg(image: Image.Image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue())


def bytes_to_jpeg_bytes(raw_img):
    return PIL_to_jpeg(bytes_to_PIL(raw_img))


class LLMOpenAI:

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
        self.client = OAsyncClient(host=host)
        self.prompt = prompt
        self.model = model
        self.image_token = image_token
        self.base_template = base_template
        self.user_template = user_template
        self.assistant_template = assistant_template

    def _format_prompt_unfinished_prompt(self, user_prompt: str, assistant_text: str):
        return f"{self.base_template}{self.user_template.start}{self.image_token}{user_prompt}{self.user_template.end}{self.assistant_template.start}{assistant_text}"

    async def complete(self, assistant_start: str, image: str) -> str:
        image = bytes_to_jpeg_bytes(image)

        output = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                        },
                    ],
                }
            ],
        )

        return assistant_start + output.response

    # except ollama.ResponseError:
    #     return "The analysis server seems to be offline!"

    async def generate(self, image: str) -> str:
        image = bytes_to_jpeg_bytes(image)

        output = await self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": self.prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image}",
                        },
                    ],
                }
            ],
        )

        return output.response

    # except ollama.ResponseError:
    #     return "The analysis server seems to be offline!"


class LLMOllama:

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
