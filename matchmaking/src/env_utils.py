from pathlib import Path

from dotenv import load_dotenv


def load_project_env(start_path: Path) -> None:
    for directory in [start_path, *start_path.parents]:
        env_path = directory / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break
