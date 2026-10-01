from urllib.parse import urlsplit

from app.providers.http_transport import BoundedHTTP, ExternalServiceError


def official_base(value: str) -> str:
    base = (value or "https://api.openai.com/v1").rstrip("/")
    try:
        url = urlsplit(base)
        port = url.port
    except ValueError as exc:
        raise ExternalServiceError("官方服务地址必须为 https://api.openai.com/v1。") from exc
    if (
        url.scheme != "https"
        or url.hostname != "api.openai.com"
        or port not in (None, 443)
        or url.path != "/v1"
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ExternalServiceError("官方服务地址必须为 https://api.openai.com/v1。")
    return base


class OpenAIHTTP(BoundedHTTP):
    validate_base = staticmethod(official_base)
