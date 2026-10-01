import json

import httpx


class ExternalServiceError(Exception):
    def __init__(self, message, code="unavailable", retryable=False):
        self.message, self.code, self.retryable = message, code, retryable


class BoundedHTTP:
    """Bounded HTTP transport. No redirects, URL downloads or automatic billable retries."""

    def __init__(self, key, base="", timeout=180, transport=None):
        self.key, self.base, self.timeout, self.transport = key, base, timeout, transport

    async def post(self, endpoint, *, max_bytes=128 * 1024 * 1024, **kwargs):
        if not self.key:
            raise ExternalServiceError("未配置 API Key，请在服务端 .env 配置后重启。")
        url = self.validate_base(self.base) + endpoint
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, transport=self.transport, follow_redirects=False
            ) as client:
                async with client.stream(
                    "POST", url, headers={"Authorization": "Bearer " + self.key}, **kwargs
                ) as response:
                    if response.status_code >= 300:
                        if response.status_code in (401, 403):
                            raise ExternalServiceError("API 认证失败或当前账户无模型访问权限。")
                        if response.status_code == 429:
                            raise ExternalServiceError(
                                "服务限流或账户额度不足，请检查账户。", retryable=True
                            )
                        if response.status_code == 400:
                            raise ExternalServiceError(
                                "服务拒绝了请求，请检查模型配置及输入内容。", "invalid_input"
                            )
                        raise ExternalServiceError(
                            "外部服务暂时不可用，请稍后重试。", retryable=True
                        )
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > max_bytes:
                            raise ExternalServiceError("外部服务返回的数据过大。", "invalid_result")
                    value = json.loads(data)
                    if not isinstance(value, dict):
                        raise ValueError()
                    return value, response.headers.get("x-request-id", "")[:200]
        except httpx.TimeoutException as exc:
            raise ExternalServiceError(
                "外部服务响应超时；请求可能已计费，重试前请检查账户用量。", "timeout", True
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError("无法连接外部服务，请检查网络。", retryable=True) from exc
        except (ValueError, UnicodeError) as exc:
            raise ExternalServiceError("外部服务返回的数据格式无效。", "invalid_result") from exc
