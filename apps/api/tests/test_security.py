import uuid

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip():
    encoded = hash_password("a-long-development-password")
    assert encoded != "a-long-development-password"
    assert verify_password("a-long-development-password", encoded)


def test_access_token_contains_subject():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    claims = decode_token(token)
    assert claims["sub"] == str(user_id)
    assert claims["typ"] == "access"
