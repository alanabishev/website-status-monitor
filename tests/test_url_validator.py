import pytest
from src.url_validator import (
    is_website_url_valid,
    get_formatted_url,
    InvalidUrlException,
)


def test_is_website_url_valid():
    assert is_website_url_valid("http://example.com")
    assert is_website_url_valid("https://example.com")
    assert is_website_url_valid("example.com")
    assert is_website_url_valid("www.example.com")
    assert is_website_url_valid("localhost")
    assert not is_website_url_valid("not a url")
    assert not is_website_url_valid("examplecom")
    assert not is_website_url_valid("https://")
    assert not is_website_url_valid("https://example")
    assert not is_website_url_valid("https://example..")


def test_get_formatted_url():
    assert get_formatted_url("http://example.com") == "example.com"
    assert get_formatted_url("https://example.com") == "example.com"
    assert get_formatted_url("www.example.com") == "example.com"
    assert get_formatted_url("localhost") == "localhost"
    assert get_formatted_url("192.168.1.1") == "192.168.1.1"


def test_get_formatted_url_invalid():
    with pytest.raises(InvalidUrlException):
        get_formatted_url("not a url")


def test_get_formatted_url_skip_validation():
    assert get_formatted_url("not a url", skip_validation=True) == "not a url"
