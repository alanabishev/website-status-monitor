"""
This module provides functions for URL validation and formatting.
Credits: URL validation regex is sourced from Django's url validation:
https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45
"""

import re
from urllib.parse import urlparse

URL_VALIDITY_REGEX = re.compile(
    r"^(?:http(s)?://)?"  # optional http/https
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",  # path
    re.IGNORECASE,
)


def is_website_url_valid(url: str) -> bool:
    """Check if the given URL is valid.

    Args:
        url (str): The URL to be validated.

    Returns:
        bool: True if URL is valid, False otherwise.
    """
    return re.match(URL_VALIDITY_REGEX, url) is not None


def get_formatted_url(url: str, skip_validation: bool = False) -> str:
    """Format the given URL to remove 'www.' and convert to lowercase.

    Args:
        url (str): The URL to be formatted.
        skip_validation (bool): If True, skips validation check. Defaults to False.

    Returns:
        str: Formatted URL.

    Raises:
        InvalidUrlException: If URL is not valid.
    """
    if not skip_validation and not is_website_url_valid(url):
        raise InvalidUrlException(url)

    parser = urlparse(url)
    clean_url = parser.netloc or parser.path.split("/")[0]
    return clean_url.lstrip("www.").lower()


class InvalidUrlException(Exception):
    """Exception raised for invalid URLs."""

    def __init__(self, url: str):
        self.url = url
        self.message = f"Invalid URL provided: {self.url}"
        super().__init__(self.message)
