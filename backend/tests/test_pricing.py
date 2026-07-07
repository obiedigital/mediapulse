from mediapulse.ai.pricing import estimate_cost_usd


def test_sonnet_pricing():
    cost = estimate_cost_usd("claude-sonnet-4-6", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == 3.0 + 15.0


def test_opus_more_expensive_than_sonnet_than_haiku():
    opus = estimate_cost_usd("claude-opus-4-8", input_tokens=1000, output_tokens=1000)
    sonnet = estimate_cost_usd("claude-sonnet-4-6", input_tokens=1000, output_tokens=1000)
    haiku = estimate_cost_usd("claude-haiku-4-5", input_tokens=1000, output_tokens=1000)
    assert opus > sonnet > haiku


def test_unknown_model_returns_none_not_a_guess():
    assert estimate_cost_usd("some-future-model-xyz", input_tokens=1000, output_tokens=1000) is None


def test_zero_tokens_is_zero_cost():
    assert estimate_cost_usd("claude-sonnet-4-6", input_tokens=0, output_tokens=0) == 0.0
