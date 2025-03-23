import pytest

from .logic import generate_ai_photo


@pytest.mark.asyncio
async def test_generate_ai_photo_success():
    output = await generate_ai_photo(prompt="Generate a car in a middle of the field")
    with open('output.png', 'wb') as f:
        f.write(output)
    assert output is not None
