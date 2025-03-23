from shared import get_replicate_client

__all__ = ("generate_ai_photo",)


async def generate_ai_photo(prompt: str) -> bytes:
    replicate_client = get_replicate_client()

    output = replicate_client.run(
        "black-forest-labs/flux-dev",
        input={"prompt": prompt}
        )
    return output[0].read()
