from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_token_round_trip() -> None:
    password = "correct horse battery staple"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash)
    assert not verify_password("wrong password", password_hash)
    assert decode_access_token(create_access_token("42")) == "42"
