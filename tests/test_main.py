import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from http import HTTPStatus

from src.main import app, DatabaseManager, WebsiteMonitor, WebsiteInfo


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_manager_mock():
    return Mock(spec=DatabaseManager)


@pytest.fixture
def website_monitor_mock():
    return AsyncMock(spec=WebsiteMonitor)


def test_create_website_info(client, db_manager_mock, website_monitor_mock):
    db_manager_mock.get_website_data.side_effect = [None, MagicMock()]
    app.state.db_manager = db_manager_mock
    app.state.website_monitor = website_monitor_mock

    website_info = WebsiteInfo(url="http://example.com", interval=30)
    response = client.post("/create_website_info", json=website_info.dict())

    assert response.status_code == HTTPStatus.CREATED.value
    assert response.json() == {"message": "Website added to monitoring"}


def test_create_website_info_existing_url(client, db_manager_mock):
    db_manager_mock.get_website_data.return_value = [
        {"url": "http://example.com", "interval": 30}
    ]
    app.state.db_manager = db_manager_mock

    website_info = WebsiteInfo(url="http://example.com", interval=30)
    response = client.post("/create_website_info", json=website_info.dict())

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert response.json() == {"detail": "Website with URL example.com already exists"}


def test_update_website_info(client, db_manager_mock):
    db_manager_mock.get_website_data.return_value = [
        {"url": "http://example.com", "interval": 30}
    ]
    app.state.db_manager = db_manager_mock

    website_info = WebsiteInfo(url="http://example.com", interval=60)
    response = client.patch("/update_website_info", json=website_info.dict())

    assert response.status_code == HTTPStatus.OK.value
    assert response.json() == {
        "message": "Website info changed, it will be applied during the next run of the app"
    }


def test_update_website_info_non_existing_url(client, db_manager_mock):
    db_manager_mock.get_website_data.return_value = []
    app.state.db_manager = db_manager_mock

    website_info = WebsiteInfo(url="http://nonexistent.com", interval=60)
    response = client.patch("/update_website_info", json=website_info.dict())

    assert response.status_code == HTTPStatus.NOT_FOUND.value
    assert response.json() == {"detail": "Website with URL nonexistent.com not found"}


def test_update_website_info_no_interval_no_regexp(client, db_manager_mock):
    db_manager_mock.get_website_data.return_value = [
        {"url": "http://example.com", "interval": 30}
    ]
    app.state.db_manager = db_manager_mock

    website_info = WebsiteInfo(url="http://example.com")
    response = client.patch("/update_website_info", json=website_info.dict())

    assert response.status_code == HTTPStatus.BAD_REQUEST.value
    assert response.json() == {"detail": "Interval or regexp_pattern should be filled"}
