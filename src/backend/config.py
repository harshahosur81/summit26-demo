import os
import secrets
from pathlib import Path
from typing import Optional

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "src" / "backend" / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

def generate_vault_secret() -> str:
    """Generates a secure 32-character cryptographic secret."""
    return secrets.token_urlsafe(24)[:32]

def ensure_env_file_with_vault_secret() -> str:
    """
    Ensures that a .env file exists and contains a non-empty VAULT_SECRET.
    If the file is missing or VAULT_SECRET is not set, it generates one
    and writes/updates the .env file.
    """
    lines = []
    vault_secret = ""
    env_exists = ENV_PATH.exists()

    if env_exists:
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()
        
        # Parse for existing VAULT_SECRET
        secret_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("VAULT_SECRET="):
                parts = line.split("=", 1)
                val = parts[1].strip().strip("\"'")
                if val:
                    vault_secret = val
                secret_found = True
                break
        
        if not vault_secret:
            # Secret is missing or empty inside existing .env, let's insert/update it
            vault_secret = generate_vault_secret()
            if secret_found:
                # Update existing line
                for i, line in enumerate(lines):
                    if line.strip().startswith("VAULT_SECRET="):
                        lines[i] = f'VAULT_SECRET="{vault_secret}"\n'
                        break
            else:
                # Append line
                lines.append(f'\nVAULT_SECRET="{vault_secret}"\n')
            
            with open(ENV_PATH, "w") as f:
                f.writelines(lines)
    else:
        # Create new .env file with default parameters
        vault_secret = generate_vault_secret()
        default_env = (
            f'VAULT_SECRET="{vault_secret}"\n'
            f'TESLA_EMAIL="user@example.com"\n'
            f'INVERTER_IP="192.168.1.150"\n'
            f'PORT=8888\n'
            f'EMA_ALPHA=0.1\n'
            f'GRID_PHASES=3\n'
            f'OVERRIDE_DURATION_MINS=120\n'
        )
        with open(ENV_PATH, "w") as f:
            f.write(default_env)

    return vault_secret

# Ensure .env is set up and load variables
_vault_secret_from_file = ensure_env_file_with_vault_secret()

# Simple env loader
def get_env_str(key: str, default: str) -> str:
    # Try OS env first, then look at .env file manually if needed
    val = os.getenv(key)
    if val is not None:
        return val
    
    if ENV_PATH.exists():
        with open(ENV_PATH, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    return default

def get_env_float(key: str, default: float) -> float:
    try:
        return float(get_env_str(key, str(default)))
    except ValueError:
        return default

def get_env_int(key: str, default: int) -> int:
    try:
        return int(get_env_str(key, str(default)))
    except ValueError:
        return default

# Configuration Class
class AppConfig:
    PORT: int = get_env_int("PORT", 8888)
    VAULT_SECRET: str = os.getenv("VAULT_SECRET", _vault_secret_from_file)
    TESLA_EMAIL: str = get_env_str("TESLA_EMAIL", "user@example.com")
    INVERTER_IP: Optional[str] = os.getenv("INVERTER_IP") or (
        get_env_str("INVERTER_IP", "") if get_env_str("INVERTER_IP", "") else None
    )
    EMA_ALPHA: float = get_env_float("EMA_ALPHA", 0.1)
    
    # Grid math parameters
    GRID_PHASES: int = get_env_int("GRID_PHASES", 3)  # 1 or 3 phases
    OVERRIDE_DURATION_MINS: int = get_env_int("OVERRIDE_DURATION_MINS", 120)
    
    # Path to SQLite Database
    DATABASE_PATH: Path = DATA_DIR / "solar_sync.db"
    
    # Helper to check if Mock Modes are active
    @property
    def is_mock_tesla(self) -> bool:
        return not self.TESLA_EMAIL or self.TESLA_EMAIL.lower() == "user@example.com"
        
    @property
    def is_mock_inverter(self) -> bool:
        return not self.INVERTER_IP

config = AppConfig()
