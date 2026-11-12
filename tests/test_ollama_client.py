import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from src.agent.llm import OllamaClient
from src.agent.instructions import SYSTEM_INSTRUCTIONS

@pytest.mark.asyncio
@pytest.mark.integration
async def test_ollama_generates_response():
    client = OllamaClient()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTIONS,
        },
        {
            "role": "user",
            "content": (
                "A caller is looking for a safe living arrangement "
                "for their 82-year-old mother. Respond empathetically "
                "and ask one thoughtful follow-up question."
            ),
        },
    ]

    response = await client.chat(messages)

    assert isinstance(response, str)
    assert len(response.strip()) > 0

    print("\nLlama response:")
    print(response)

@pytest.mark.asyncio
async def test_ollama_client_returns_response(monkeypatch):
    settings = MagicMock()
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_model = "llama3.2:3b"

    monkeypatch.setattr(
        "src.agent.llm.get_settings",
        lambda: settings,
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Hello, how can I help?"},
        "total_duration": 100,
    }
    mock_response.raise_for_status.return_value = None

    mock_post = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = mock_post

    monkeypatch.setattr(
        "src.agent.llm.httpx.AsyncClient",
        lambda **kwargs: mock_client,
    )

    client = OllamaClient()

    response = await client.chat([
        {"role": "user", "content": "Hello"}
    ])

    assert response == "Hello, how can I help?"
    mock_post.assert_awaited_once()

    call_args = mock_post.await_args

    assert call_args.args[0] == (
        "http://localhost:11434/api/chat"
    )
    assert call_args.kwargs["json"]["model"] == "llama3.2:3b"

@pytest.mark.asyncio
async def test_ollama_client_propagates_connection_error(monkeypatch):
    settings = MagicMock()
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_model = "llama3.2:3b"

    monkeypatch.setattr(
        "src.agent.llm.get_settings",
        lambda: settings,
    )

    mock_post = AsyncMock(
        side_effect=httpx.ConnectError("Ollama is unavailable")
    )

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = mock_post

    monkeypatch.setattr(
        "src.agent.llm.httpx.AsyncClient",
        lambda **kwargs: mock_client,
    )

    client = OllamaClient()

    with pytest.raises(httpx.ConnectError):
        await client.chat([
            {"role": "user", "content": "Hello"}
        ])

@pytest.mark.asyncio
async def test_ollama_client_recovers_after_connection_failure(monkeypatch):
    settings = MagicMock()
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_model = "llama3.2:3b"

    monkeypatch.setattr(
        "src.agent.llm.get_settings",
        lambda: settings,
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Connection recovered."},
    }
    mock_response.raise_for_status.return_value = None

    mock_post = AsyncMock(
        side_effect=[
            httpx.ConnectError("Temporary connection failure"),
            mock_response,
        ]
    )

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = mock_post

    monkeypatch.setattr(
        "src.agent.llm.httpx.AsyncClient",
        lambda **kwargs: mock_client,
    )

    client = OllamaClient()

    response = await client.chat([
        {"role": "user", "content": "Hello"}
    ])

    assert response == "Connection recovered."
    assert mock_post.await_count == 2

@pytest.mark.asyncio
async def test_ollama_client_does_not_retry_http_errors(monkeypatch):
    settings = MagicMock()
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_model = "llama3.2:3b"

    monkeypatch.setattr(
        "src.agent.llm.get_settings",
        lambda: settings,
    )

    mock_post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
            response=httpx.Response(
                500,
                request=httpx.Request("POST", "http://localhost:11434/api/chat"),
            ),
        )
    )

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = mock_post

    monkeypatch.setattr(
        "src.agent.llm.httpx.AsyncClient",
        lambda **kwargs: mock_client,
    )

    client = OllamaClient()

    with pytest.raises(httpx.HTTPStatusError):
        await client.chat([
            {"role": "user", "content": "Hello"}
        ])

    assert mock_post.await_count == 1