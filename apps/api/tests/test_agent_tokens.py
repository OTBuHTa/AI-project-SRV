from app.api.v1.agents import _hash_token, _new_token


def test_agent_tokens_are_random_and_hashed():
    first, first_hash = _new_token("agent")
    second, second_hash = _new_token("agent")
    assert first.startswith("agent_")
    assert first != second
    assert first_hash != first
    assert first_hash != second_hash
    assert _hash_token(first) == first_hash
