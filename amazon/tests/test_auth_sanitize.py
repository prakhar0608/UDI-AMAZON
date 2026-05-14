import pytest

from amazon_ads_app.auth import token_fingerprint, validate_bearer_token_string


def test_validate_bearer_accepts_long_token():
    t = "a" * 32
    assert validate_bearer_token_string(t) == t


def test_validate_bearer_strips_edges():
    t = "b" * 24
    assert validate_bearer_token_string(f"  {t}  ") == t


def test_validate_bearer_rejects_inner_whitespace():
    with pytest.raises(ValueError, match="whitespace"):
        validate_bearer_token_string("a" * 20 + " " + "b" * 20)


def test_validate_bearer_rejects_bearer_prefix():
    with pytest.raises(ValueError, match="Bearer. prefix"):
        validate_bearer_token_string("Bearer" + "x" * 30)


def test_validate_bearer_rejects_too_short():
    with pytest.raises(ValueError, match="short"):
        validate_bearer_token_string("short")


def test_token_fingerprint_stable():
    fp = token_fingerprint("abc" * 10)
    assert fp["len"] == 30
    assert len(str(fp["sha256_prefix"])) == 8
