import os
from pathlib import Path

from dotenv import load_dotenv


def load_project_env(start_path: Path) -> None:
    for directory in [start_path, *start_path.parents]:
        env_path = directory / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break


def get_cors_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    if origins:
        return origins

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
