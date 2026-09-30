from collections.abc import Callable, Mapping

from app.core.config import get_settings
from app.providers.contracts import ImageProvider
from app.providers.mock import MockImageProvider
from app.providers.openai_images import OpenAIImageProvider


class ProviderUnavailable(Exception):
    pass


class ProviderRouter:
    """Select an explicitly configured provider; never silently fall back to Mock."""

    def __init__(
        self,
        name: str | None = None,
        factories: Mapping[str, Callable[[], ImageProvider]] | None = None,
    ):
        self.name = get_settings().image_provider if name is None else name
        self.factories = (
            {"mock": MockImageProvider, "openai": OpenAIImageProvider}
            if factories is None
            else dict(factories)
        )

    def select(self) -> ImageProvider:
        factory = self.factories.get(self.name)
        if factory is None:
            raise ProviderUnavailable
        return factory()
