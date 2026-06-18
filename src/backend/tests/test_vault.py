import pytest
import pytest_asyncio
from src.backend.database import init_db
from src.backend.vault import CryptographicVault, derive_key, encrypt_data, decrypt_data

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Initializes the database schema before each test run."""
    await init_db()

@pytest.mark.asyncio
async def test_key_derivation():
    password = "super_secret_test_password"
    salt = b"0123456789abcdef"
    
    key1 = derive_key(password, salt)
    key2 = derive_key(password, salt)
    
    assert len(key1) == 32
    assert key1 == key2
    
    key3 = derive_key(password, b"different_salt_12")
    assert key1 != key3

@pytest.mark.asyncio
async def test_aes_gcm_encrypt_decrypt():
    password = "super_secret_test_password"
    salt = b"0123456789abcdef"
    key = derive_key(password, salt)
    
    original_text = '{"access_token": "abc123xyz", "refresh_token": "ref987", "expires_in": 3600}'
    
    encrypted_payload = encrypt_data(original_text, key)
    assert len(encrypted_payload) > 28
    
    decrypted_text = decrypt_data(encrypted_payload, key)
    assert decrypted_text == original_text

@pytest.mark.asyncio
async def test_vault_save_load():
    test_json = '{"token": "test-token-value-123"}'
    
    CryptographicVault.delete_tesla_cache()
    
    loaded = await CryptographicVault.load_tesla_cache()
    assert loaded is None
    
    await CryptographicVault.save_tesla_cache(test_json)
    
    loaded_json = await CryptographicVault.load_tesla_cache()
    assert loaded_json == test_json
    
    CryptographicVault.delete_tesla_cache()

@pytest.mark.asyncio
async def test_vault_save_load_sync():
    test_json = '{"token": "sync-token-value-456"}'
    
    CryptographicVault.delete_tesla_cache()
    
    # Initialize the key
    await CryptographicVault.get_key()
    
    # Try load sync
    loaded = CryptographicVault.load_tesla_cache_sync()
    assert loaded is None
    
    # Save sync
    CryptographicVault.save_tesla_cache_sync(test_json)
    
    # Load sync
    loaded_json = CryptographicVault.load_tesla_cache_sync()
    assert loaded_json == test_json
    
    CryptographicVault.delete_tesla_cache()
