import requests
import httpx
from typing import Dict, Optional


def strip_think(text: str) -> str:
    return text.split("</think>")[-1]


class ClientBase:
    def query(
        self, user_prompt: str, system_prompt: str, verbose: bool, **use_options
    ) -> str: ...
    async def async_query(
        self, user_prompt: str, system_prompt: str, verbose: bool, **use_options
    ) -> str: ...


class OllamaClient(ClientBase):
    def __init__(self, model: str, url: str = "http://localhost:11434/api/chat"):
        super().__init__()
        self.url = url
        self.model = model

    def query(
        self,
        user_prompt: str,
        system_prompt: str,
        options: Dict = {},
        format_obj: Optional[Dict] = None,
        verbose: bool = False,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": options,
            "stream": False,
        }

        if format_obj is not None:
            payload["format"] = {"type": "object", **format_obj}

        response = requests.post(self.url, json=payload)
        response.raise_for_status()

        data = response.json()
        output = data.get("message", {}).get("content", "")

        return output.strip() if verbose else strip_think(output).strip()

    async def async_query(
        self,
        user_prompt: str,
        system_prompt: str,
        options: Dict = {},
        format_obj: Optional[Dict] = None,
        verbose: bool = False,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": options,
            "stream": False,
        }

        if format_obj is not None:
            payload["format"] = {"type": "object", **format_obj}

        timeout = httpx.Timeout(120.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()

        output = data.get("message", {}).get("content", "")

        return output.strip() if verbose else strip_think(output).strip()


class OpenAIClient(ClientBase):
    def __init__(
        self,
        model: str,
        url: str = "http://localhost:8000/v1",
        api_key: str = "not-needed",
    ):
        from openai import OpenAI, AsyncOpenAI

        super().__init__()
        self.client = OpenAI(base_url=url, api_key=api_key)
        self.async_client = AsyncOpenAI(base_url=url, api_key=api_key)
        self.model = model

    def query(
        self,
        user_prompt: str,
        system_prompt: str,
        options: Dict = {},
        format_obj: Optional[Dict] = None,
        verbose: bool = False,
    ):
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **options,
        }

        if format_obj is not None:
            request_body["extra_body"] = {"guided_json": format_obj}

        raw_response = self.client._client.request(
            method="POST", url="/chat/completions", json=request_body
        )
        response = raw_response.json()

        output = response["choices"][0]["message"]["content"]

        if verbose:
            return output
        else:
            return strip_think(output)

    async def async_query(
        self,
        user_prompt: str,
        system_prompt: str,
        options: Dict = {},
        format_obj: Optional[Dict] = None,
        verbose: bool = False,
    ) -> str:
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **options,
        }

        if format_obj is not None:
            request_body["extra_body"] = {"guided_json": format_obj}

        response = await self.client.chat.completions.create(**request_body)
        output = response.choices[0].message.content

        return output if verbose else strip_think(output)


class Qwen3OllamaClient(OllamaClient):
    def __init__(
        self, url: str = "http://localhost:11434/api/chat", model: str = "qwen3:8b"
    ):
        super().__init__(url=url, model=model)

    def query(
        self, user_prompt: str, system_prompt: str, verbose: bool = False, **use_options
    ) -> str:
        options = {
            "temperature": use_options.get("temperature", 0.7),
            "top_p": 0.8,
            "top_k": 20,
            "presence_penalty": 1.5,
            "mirostat": 0,
            "frequency_penalty": 0.0,
        }

        return super().query(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            options=options,
            format_obj=use_options.get("format_obj"),
            verbose=verbose,
        )

    async def async_query(
        self, user_prompt: str, system_prompt: str, verbose: bool = False, **use_options
    ) -> str:
        options = {
            "temperature": use_options.get("temperature", 0.7),
            "top_p": 0.8,
            "top_k": 20,
            "presence_penalty": 1.5,
            "mirostat": 0,
            "frequency_penalty": 0.0,
        }

        return await super().async_query(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            options=options,
            format_obj=use_options.get("format_obj"),
            verbose=verbose,
        )


class Qwen3OpenAiClient(OpenAIClient):

    def __init__(
        self,
        model: str,
        url: str = "http://localhost:8000/v1",
        api_key: str = "not-needed",
    ):
        from openai import OpenAI

        super().__init__(model=model, url=url, api_key=api_key)

    def query(
        self, user_prompt: str, system_prompt: str, verbose: bool = False, **use_options
    ):
        options = {
            "temperature": use_options.get("temperature", 0.7),
            "top_p": 0.8,
            "top_k": 20,
            "min_p": 0,
            "presence_penalty": 1.5,
        }

        return super().query(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            options=options,
            format_obj=use_options.get("format_obj"),
            verbose=verbose,
        )

    async def async_query(
        self, user_prompt: str, system_prompt: str, verbose: bool = False, **use_options
    ):
        options = {
            "temperature": use_options.get("temperature", 0.7),
            "top_p": 0.8,
            "top_k": 20,
            "min_p": 0,
            "presence_penalty": 1.5,
        }

        return await super().async_query(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            options=options,
            format_obj=use_options.get("format_obj"),
            verbose=verbose,
        )


class GptOssClient(OpenAIClient):
    def __init__(
        self,
        model: str,
        url: str = "http://localhost:8000/v1",
        api_key: str = "not-needed",
    ):
        super().__init__(model=model, url=url, api_key=api_key)

    def query(
        self, user_prompt: str, system_prompt: str, verbose: bool = False, **use_options
    ):
        options = {
            "temperature": user_prompt.get("temperature", 1.0),
            "top_p": 1.0,
        }

        return super().query(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            options=options,
            format_obj=use_options.get("format_obj"),
            verbose=verbose,
        )

    async def async_query(
        self, user_prompt: str, system_prompt: str, verbose: bool = False, **use_options
    ):
        options = {
            "temperature": user_prompt.get("temperature", 1.0),
            "top_p": 1.0,
        }

        return await super().async_query(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            options=options,
            format_obj=use_options.get("format_obj"),
            verbose=verbose,
        )
