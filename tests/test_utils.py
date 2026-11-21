"""clip shortens a long logged value and leaves a short one alone."""
from inkcut.core.utils import clip


def test_clip_shortens_a_long_string():
    result = clip("a" * 1001)
    assert result == ("a" * 1000) + "..."
    assert len(result) == 1003
    assert result.endswith("...")


def test_clip_leaves_a_short_string_unchanged():
    value = "short"
    assert clip(value) == value
