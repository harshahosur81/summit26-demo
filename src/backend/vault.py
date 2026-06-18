import aiosqlite
import logging
import secrets
from pathlib import Path
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from src.backend.config import config

logger = logging.getLogger("solar_sync.vault")

# Path where encrypted cache is stored
ENCRYPTED_CACHE_PATH = config.DATABASE_PATH.parent / ".cache.enc"

async def get_or_create_salt() -> bytes:
    """Retrieves or creates a 16-byte salt from the database system_config table."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute("SELECT value FROM system_config WHERE key = 'vault_salt'") as cursor:
            row = await cursor.fetchone()
            if row:
                return bytes.fromhex(row[0])
        
        # Generates a new cryptographically secure 16-byte salt
        salt = secrets.token_bytes(16)
        salt_hex = salt.hex()
        await db.execute(
            "INSERT INTO system_config (key, value) VALUES ('vault_salt', ?)",
            (salt_hex,)
        )
        await db.commit()
        logger.info("Generated new cryptographic salt for vault.")
        return salt

def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 256-bit AES key from password and salt using PBKDF2 with 100,000 iterations."""
    # PBKDF2 parameters as specified in SDD requirements
    iterations = 100000
    return PBKDF2(password, salt, dkLen=32, count=iterations, hmac_hash_module=SHA256)

def encrypt_data(plaintext: str, key: bytes) -> bytes:
    """
    Encrypts plaintext using AES-256-GCM.
    Returns: nonce (12 bytes) + tag (16 bytes) + ciphertext
    """
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    # Pack: nonce (12 bytes) + tag (16 bytes) + ciphertext
    return cipher.nonce + tag + ciphertext

def decrypt_data(payload: bytes, key: bytes) -> str:
    """
    Decrypts AES-256-GCM encrypted payload.
    Payload expected: nonce (16 bytes) + tag (16 bytes) + ciphertext
    """
    if len(payload) < 32:
        raise ValueError("Encrypted payload is too short or malformed.")
    
    nonce = payload[:16]
    tag = payload[16:32]
    ciphertext = payload[32:]
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext_bytes.decode('utf-8')

class CryptographicVault:
    """Coordinates secure storage and loading of the encrypted Tesla token cache file."""
    
    _derived_key: Optional[bytes] = None
    
    @classmethod
    async def get_key(cls) -> bytes:
        """Loads salt from DB, derives key if not already cached in memory."""
        if cls._derived_key is not None:
            return cls._derived_key
            
        salt = await get_or_create_salt()
        # Derive key using our secure password
        cls._derived_key = derive_key(config.VAULT_SECRET, salt)
        return cls._derived_key

    @classmethod
    async def save_tesla_cache(cls, cache_json_content: str):
        """Encrypts and writes TeslaPy cache JSON content to .cache.enc."""
        try:
            key = await cls.get_key()
            encrypted_payload = encrypt_data(cache_json_content, key)
            
            # Write to file
            with open(ENCRYPTED_CACHE_PATH, "wb") as f:
                f.write(encrypted_payload)
            logger.info("Tesla token cache safely encrypted and saved to disk.")
        except Exception as e:
            logger.error(f"Failed to encrypt and save Tesla cache: {e}")
            raise

    @classmethod
    async def load_tesla_cache(cls) -> Optional[str]:
        """Reads, decrypts, and returns TeslaPy cache JSON content. Returns None if cache doesn't exist."""
        if not ENCRYPTED_CACHE_PATH.exists():
            logger.debug("No encrypted Tesla cache file found on disk.")
            return None
            
        try:
            with open(ENCRYPTED_CACHE_PATH, "rb") as f:
                encrypted_payload = f.read()
                
            key = await cls.get_key()
            decrypted_str = decrypt_data(encrypted_payload, key)
            logger.info("Tesla token cache safely loaded and decrypted in-memory.")
            return decrypted_str
        except Exception as e:
            logger.error(f"Failed to read or decrypt Tesla cache: {e}")
            raise ValueError(f"Vault decryption failed. Check your VAULT_SECRET or database salt integrity: {e}")
            
    @classmethod
    def save_tesla_cache_sync(cls, cache_json_content: str):
        """Synchronously encrypts and writes TeslaPy cache JSON content. Requires get_key() to have run on startup."""
        if cls._derived_key is None:
            raise RuntimeError("CryptographicVault key is not derived yet. Await CryptographicVault.get_key() on startup.")
        try:
            encrypted_payload = encrypt_data(cache_json_content, cls._derived_key)
            with open(ENCRYPTED_CACHE_PATH, "wb") as f:
                f.write(encrypted_payload)
            logger.info("Tesla token cache safely encrypted and saved to disk (sync).")
        except Exception as e:
            logger.error(f"Failed to encrypt and save Tesla cache (sync): {e}")
            raise

    @classmethod
    def load_tesla_cache_sync(cls) -> Optional[str]:
        """Synchronously reads and decrypts TeslaPy cache JSON content. Requires get_key() to have run on startup."""
        if cls._derived_key is None:
            raise RuntimeError("CryptographicVault key is not derived yet. Await CryptographicVault.get_key() on startup.")
        if not ENCRYPTED_CACHE_PATH.exists():
            return None
        try:
            with open(ENCRYPTED_CACHE_PATH, "rb") as f:
                encrypted_payload = f.read()
            decrypted_str = decrypt_data(encrypted_payload, cls._derived_key)
            logger.info("Tesla token cache safely loaded and decrypted in-memory (sync).")
            return decrypted_str
        except Exception as e:
            logger.error(f"Failed to read or decrypt Tesla cache (sync): {e}")
            raise

    @classmethod
    def delete_tesla_cache(cls):
        """Deletes the encrypted cache file from disk."""
        if ENCRYPTED_CACHE_PATH.exists():
            ENCRYPTED_CACHE_PATH.unlink()
            logger.info("Encrypted Tesla token cache file removed.")
