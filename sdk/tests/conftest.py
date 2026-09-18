import pytest

from aifootprint import AIClient

BASE_URL = "http://testserver"


@pytest.fixture
def client():
    """A client whose httpx.Client is intercepted by pytest_httpx's
    `httpx_mock` fixture (auto-used transitively via the `httpx_mock`
    parameter in each test) - no real network call is ever made in the
    unit test suite.
    """
    c = AIClient(api_key="afp_test_key", base_url=BASE_URL)
    yield c
    c.close()


@pytest.fixture
def unauthenticated_client():
    c = AIClient(base_url=BASE_URL)
    yield c
    c.close()
