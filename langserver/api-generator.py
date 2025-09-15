import os
import secrets
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE_FILE = ROOT_DIR / ".env.example"

def generate_api_key(length: int = 64) -> str:
    return secrets.token_hex(length // 2)

def ensure_env_file():
    if not ENV_FILE.exists():
        if not ENV_EXAMPLE_FILE.exists():
            raise FileNotFoundError(
                f"{ENV_EXAMPLE_FILE} not found. Cannot create {ENV_FILE}."
            )
        shutil.copy(ENV_EXAMPLE_FILE, ENV_FILE)
        print(f"{ENV_FILE} created from {ENV_EXAMPLE_FILE}.")

def update_api_key_in_env(api_key: str):
    updated = False
    lines = []

    with ENV_FILE.open("r") as f:
        for line in f:
            if line.strip().startswith("API_KEY="):
                lines.append(f"API_KEY={api_key}\n")
                updated = True
            else:
                lines.append(line)

    if not updated:
        lines.append(f"\nAPI_KEY={api_key}\n")

    with ENV_FILE.open("w") as f:
        f.writelines(lines)

    print(f"A new API_KEY was written to {ENV_FILE}: {api_key}")

if __name__ == "__main__":
    ensure_env_file()
    new_api_key = generate_api_key()
    update_api_key_in_env(new_api_key)
