import httpx

from src.config import get_settings

class OllamaClient:
    """Client for communicating with a locally hosted Ollama model."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

        if not self.model:
            raise ValueError("OLLAMA_MODEL is not configured.")

    async def chat(
        self,
        messages: list[dict[str, str]],
        response_format: str | None = None,
    ) -> str:
        """Send conversation messages to Ollama and return its response."""

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": 200,
            },
        }

        if response_format is not None:
            if response_format != "json":
                raise ValueError("Unsupported response format.")

            payload["format"] = response_format

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()
            result = response.json()

        content = result.get("message", {}).get("content", "")

        print("\n--- OLLAMA PERFORMANCE METRICS ---")

        for metric in [
            "total_duration",
            "load_duration",
            "prompt_eval_duration",
            "eval_duration",
            "prompt_eval_count",
            "eval_count",
        ]:
            print(f"{metric}: {result.get(metric)}")

        if not content.strip():
            raise RuntimeError("Ollama returned an empty response.")

        return content.strip()
