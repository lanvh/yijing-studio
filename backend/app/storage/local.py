from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class ImageStorage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalImageStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if not candidate.is_relative_to(self.root) or candidate == self.root:
            raise ValueError("Invalid storage key.")
        return candidate

    def put(self, key: str, data: bytes) -> None:
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Generated UUID keys must never overwrite an existing file.
        try:
            with path.open("xb") as output:
                output.write(data)
        except FileExistsError:
            raise
        except OSError:
            path.unlink(missing_ok=True)
            raise

    def read(self, key: str) -> bytes:
        return self.path(key).read_bytes()

    def delete(self, key: str) -> None:
        self.path(key).unlink(missing_ok=True)


def get_image_storage() -> ImageStorage:
    settings = get_settings()
    root = Path(settings.local_storage_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[3] / root
    return LocalImageStorage(root)
