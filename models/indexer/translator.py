from .client import ClientBase

SYS_PROMPT = """Your are a professional translator. You will receive a portuguese text and you should translate it to english. If there's a better translation in the medical context, that is, it's more common to use a certain phrase / term you can change the text as long as it means the same thing. Only output the translated text and nothing more."""


async def translate(client: ClientBase, text: str, verbose: bool = False) -> str:
    return await client.async_query(text, SYS_PROMPT, verbose=verbose)
