from __future__ import annotations

"""
ManusClaw CLI entry point.
Installed via pyproject.toml [project.scripts].
"""

import asyncio
import sys


async def _run(prompt: str) -> None:
    from app.agent.manus import Manus
    from app.logger import logger

    agent = Manus()
    logger.info(f"Running Manus with prompt: {prompt[:80]}")
    result = await agent.run(prompt)
    print("\n" + "=" * 60)
    print("FINAL OUTPUT:")
    print("=" * 60)
    print(result)
    print("=" * 60)


def main() -> None:
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        try:
            prompt = input("Enter task: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

    if not prompt:
        print("No prompt provided.")
        sys.exit(1)

    asyncio.run(_run(prompt))
