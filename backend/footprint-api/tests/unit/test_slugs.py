from app.core.slugs import slugify, with_unique_suffix


def test_slugify_lowercases_and_hyphenates():
    assert slugify("My Cool Org!") == "my-cool-org"


def test_slugify_collapses_repeated_separators():
    assert slugify("a   b---c") == "a-b-c"


def test_slugify_strips_leading_and_trailing_separators():
    assert slugify("  -Hello-  ") == "hello"


def test_slugify_empty_uses_fallback():
    assert slugify("!!!", fallback="org") == "org"


def test_with_unique_suffix_differs_from_base():
    base = "my-org"
    suffixed = with_unique_suffix(base)
    assert suffixed != base
    assert suffixed.startswith("my-org-")
