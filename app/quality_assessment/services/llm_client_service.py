from dataclasses import dataclass, field
from typing import Any, Protocol

from django.conf import settings
from openrouter import OpenRouter


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMRequest:
    messages: list[LLMMessage]
    model: str | None = None
    max_tokens: int | None = None
    json_output: bool = False
    provider_options: dict[str, Any] = field(default_factory=dict)
    user_id: str | None = None


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    raw_usage: dict[str, Any] | None = None
    finish_reason: str | None = None


class LLMClient(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse:
        ...


class LLMClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class OpenRouterLLMClient:
    provider = "openrouter"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | float | None = None,
        max_tokens: int | None = None,
        http_referer: str | None = None,
        app_title: str | None = None,
        sdk_client: Any | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.model = model if model is not None else settings.LLM_MODEL
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.LLM_TIMEOUT_SECONDS
        )
        self.max_tokens = (
            max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
        )
        self.http_referer = (
            http_referer
            if http_referer is not None
            else settings.OPENROUTER_HTTP_REFERER
        )
        self.app_title = (
            app_title if app_title is not None else settings.OPENROUTER_APP_TITLE
        )
        self.sdk_client = sdk_client

    def complete(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise LLMClientError(
                "LLM API key is not configured.",
                provider=self.provider,
            )

        payload = self._payload(request)
        response = self._send(payload)
        return self._parse_response(response, payload["model"])

    def _payload(self, request: LLMRequest) -> dict[str, Any]:
        payload = {
            "model": request.model or self.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "max_tokens": request.max_tokens or self.max_tokens,
            "stream": False,
        }

        if request.json_output:
            payload["response_format"] = {"type": "json_object"}

        if request.user_id:
            payload["user"] = request.user_id

        payload.update(request.provider_options or {})
        return payload

    def _send(self, payload: dict[str, Any]) -> Any:
        try:
            if self.sdk_client is not None:
                return self.sdk_client.chat.send(**payload)

            with OpenRouter(
                api_key=self.api_key,
                http_referer=self.http_referer or None,
                x_open_router_title=self.app_title or None,
                timeout_ms=int(self.timeout_seconds * 1000),
            ) as client:
                return client.chat.send(**payload)
        except Exception as exc:
            raise LLMClientError(
                f"LLM request failed: {exc}",
                provider=self.provider,
                status_code=_error_status_code(exc),
            ) from exc

    def _parse_response(
        self,
        response: Any,
        requested_model: str,
    ) -> LLMResponse:
        choices = getattr(response, "choices", None)
        if not choices:
            raise LLMClientError(
                "LLM provider response did not include choices.",
                provider=self.provider,
            )

        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        if not isinstance(content, str):
            raise LLMClientError(
                "LLM provider response did not include message content.",
                provider=self.provider,
            )

        model = getattr(response, "model", None) or requested_model
        usage = _model_to_dict(getattr(response, "usage", None))
        finish_reason = getattr(first_choice, "finish_reason", None)

        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            raw_usage=usage,
            finish_reason=finish_reason,
        )


def get_llm_client(provider: str | None = None) -> LLMClient:
    provider_name = (provider or settings.LLM_PROVIDER).lower()

    if provider_name == "openrouter":
        return OpenRouterLLMClient()

    raise LLMClientError(f"Unsupported LLM provider: {provider_name}")


def _model_to_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump()

    dict_method = getattr(value, "dict", None)
    if callable(dict_method):
        return dict_method()

    return None


def _error_status_code(error: Exception) -> int | None:
    raw_response = getattr(error, "raw_response", None)
    return getattr(raw_response, "status_code", None)
