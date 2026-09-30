"""Run an offline Mock provider job: python -m app.mock_job --count 4."""

import argparse
import asyncio
import io

from PIL import Image
from pydantic import ValidationError

from app.core.config import get_settings
from app.providers.contracts import (
    OPERATIONS,
    GenerationRequest,
    GenerationSettings,
    ImageReference,
)
from app.providers.mock import MockImageProvider
from app.providers.router import ProviderRouter
from app.services.images import ImageService
from app.services.mock_jobs import MockJobRunner
from app.storage.local import get_image_storage


def make_demo_request(operation: str, count: int, seed: int) -> GenerationRequest:
    references = {}
    if operation != "create_character":
        output = io.BytesIO()
        Image.new("RGB", (64, 64), "#dae4ce").save(output, format="JPEG")
        image = ImageReference(data=output.getvalue())
        if operation in {"virtual_try_on", "generate_content_set"}:
            references = {"character_images": (image,), "product_images": (image,)}
        else:
            references = {"reference_images": (image,)}
    return GenerationRequest(
        operation=operation,
        prompt="Development-only synthetic sample; not a real photo.",
        settings=GenerationSettings(requested_count=count, seed=seed),
        **references,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run an offline Mock image provider test job.")
    parser.add_argument("--operation", choices=OPERATIONS, default="generate_content_set")
    parser.add_argument("--count", type=int, choices=[1, 2, 4, 6], default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--simulate-failure-at",
        type=int,
        nargs="*",
        default=[],
        help="Local testing only: 1-based output positions to fail.",
    )
    args = parser.parse_args(argv)
    if get_settings().image_provider != "mock":
        parser.error("Set IMAGE_PROVIDER=mock explicitly before running this local harness.")
    if any(index < 1 or index > args.count for index in args.simulate_failure_at):
        parser.error("Failure positions must fall within the requested count.")
    try:
        request = make_demo_request(args.operation, args.count, args.seed)
    except ValidationError:
        parser.error("Invalid generation settings.")
    service = ImageService(
        ProviderRouter(
            factories={
                "mock": lambda: MockImageProvider(fail_at=frozenset(args.simulate_failure_at))
            }
        )
    )
    try:
        key, manifest = asyncio.run(MockJobRunner(service, get_image_storage()).run(request))
    except OSError:
        parser.exit(
            1, "Could not save the local Mock job; check storage permissions and disk space.\n"
        )
    result = manifest["result"]
    status = result["metadata"].get("outcome", "FAILED")
    print(f"Mock job: {status}; {len(result['images'])}/{args.count} placeholder images.")
    print(f"Manifest storage key: {key}")
    print("These are development placeholders, not real AI photos or try-on results.")
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
