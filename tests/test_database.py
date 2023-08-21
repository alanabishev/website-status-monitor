from dataclasses import asdict
from datetime import datetime
from unittest.mock import patch, Mock, mock_open, MagicMock

import psycopg2
import pytest

from src.database_manager import DatabaseManager
from src.website_monitor import WebsiteMonitoringResult


@patch("psycopg2.connect")
def test_init(mock_connect):
    """Test that the connection is established during initialization."""
    DatabaseManager()
    assert mock_connect.called


@patch("src.database.DatabaseManager.execute_sql_file")
def test_create_tables(mock_execute_sql_file):
    """Test that the correct SQL file is executed to create tables."""
    manager = DatabaseManager()
    manager.create_tables()
    mock_execute_sql_file.assert_called_once_with(
        file_path="sql/create_tables.sql", is_return_data=False
    )


@patch("src.database.DatabaseManager.execute_sql_file")
def test_insert_website_data(mock_execute_sql_file):
    """Test that the correct SQL file is executed to insert website data."""
    manager = DatabaseManager()
    test_data = {"url": "https://example.com", "content": "Example Website"}
    manager.insert_website_data(test_data)
    mock_execute_sql_file.assert_called_once_with(
        file_path="sql/insert_website_info.sql",
        fields_data=test_data,
        is_return_data=False,
    )


@patch("psycopg2.connect")
def test_check_db(mock_connect):
    """Test that the database version is fetched correctly."""
    mock_connect.cursor.return_value.fetchone.return_value = ["13.1"]
    manager = DatabaseManager()
    manager.check_db()
    assert mock_connect.cursor.return_value.execute.called_once_with("SELECT VERSION()")


@patch("src.database.psycopg2.connect")
def test_execute_sql_file(mock_connect):
    """Test the 'execute_sql_file' function of the 'DatabaseManager' class."""
    manager = DatabaseManager()
    mock_cursor = Mock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.description = [("column1",), ("column2",)]
    mock_cursor.fetchall.return_value = [("row1", "row2")]
    test_file_path = "sql/test.sql"
    test_data = {"column1": "row1", "column2": "row2"}
    m = mock_open(read_data="SELECT * FROM table;")

    with patch("src.database.open", m):
        result = manager.execute_sql_file(test_file_path, True, test_data)

    mock_cursor.execute.assert_called_once_with(m().read(), test_data)
    assert result == [{"column1": "row1", "column2": "row2"}]


@patch("src.database.psycopg2.connect")
def test_execute_sql_file_raises_error(mock_connect):
    """Test the 'execute_sql_file' function when a database error occurs."""
    manager = DatabaseManager()
    mock_cursor = Mock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error("Database error")
    test_file_path = "sql/test.sql"
    test_data = {"column1": "row1", "column2": "row2"}
    m = mock_open(read_data="SELECT * FROM table;")

    with patch("src.database.open", m):
        with pytest.raises(psycopg2.Error):
            manager.execute_sql_file(test_file_path, True, test_data)

    mock_connect.return_value.rollback.assert_called_once()


@patch("src.database.DatabaseManager.execute_sql_file")
def test_update_website_data(mock_execute_sql_file):
    """Test that the correct SQL file is executed to update website data."""
    manager = DatabaseManager()
    test_data = {"url": "https://example.com", "content": "Updated Website"}
    manager.update_website_data(test_data)
    mock_execute_sql_file.assert_called_once_with(
        file_path="sql/update_website_info.sql",
        fields_data=test_data,
        is_return_data=False,
    )


@patch("src.database.DatabaseManager.execute_sql_file")
def test_get_website_data_all(mock_execute_sql_file):
    """Test that the correct SQL file is executed to get all website data."""
    manager = DatabaseManager()
    manager.get_website_data()
    mock_execute_sql_file.assert_called_once_with(
        file_path="sql/get_all_websites_info.sql", is_return_data=True
    )


@patch("src.database.DatabaseManager.execute_sql_file")
def test_get_website_data_single(mock_execute_sql_file):
    """Test that the correct SQL file is executed to get data of a specific website."""
    manager = DatabaseManager()
    url = "https://example.com"
    manager.get_website_data(url)
    mock_execute_sql_file.assert_called_once_with(
        file_path="sql/get_website_info.sql",
        fields_data={"url": url},
        is_return_data=True,
    )


data = [
    WebsiteMonitoringResult(
        datetime.now(), datetime.now(), 0.5, 200, "http://example.com", 1, True
    ),
    WebsiteMonitoringResult(
        datetime.now(), datetime.now(), 0.5, 200, "http://example2.com", 2, False
    ),
]
