"""
This module contains the DatabaseManager class, which encapsulates all interactions
with the PostgreSQL database.

The DatabaseManager is used to establish a connection to the database, perform basic checks,
and execute SQL queries in the form of SQL files.

In addition to the core database operations, the DatabaseManager also provides specific
methods to handle the website data and website monitoring data.

Classes:
    DatabaseManager: A class that manages all interactions with the PostgreSQL database.

"""

import logging
from dataclasses import asdict
from typing import Optional, Any

import psycopg2

from src.settings import DatabaseSettings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """A manager class for interacting with a PostgreSQL database.

    Provides methods for checking the database, executing SQL files,
    and managing website data and website monitoring data.

    Attributes:
        connection (psycopg2.extensions.connection): The connection to the database.

    """

    def __init__(self):
        """Initialize the DatabaseManager with a connection to the database."""
        self.connection = psycopg2.connect(
            host=DatabaseSettings.HOST,
            port=DatabaseSettings.PORT,
            database=DatabaseSettings.NAME,
            user=DatabaseSettings.USER,
            password=DatabaseSettings.PASSWORD,
        )

    def check_db(self) -> None:
        """check the db connection and log the version of the database."""
        query_sql = "SELECT VERSION()"
        cur = self.connection.cursor()
        cur.execute(query_sql)
        version = cur.fetchone()[0]
        logger.info("DB version = %s", version)

    def execute_sql_file(
        self,
        file_path: str,
        is_return_data: bool,
        fields_data: Optional[dict[str, Any]] = None,
    ) -> Optional[list[dict[str, Any]]]:
        """Execute a SQL file and optionally return the data.

        Args:
            file_path (str): The path to the SQL file.
            is_return_data (bool): Whether to return the data.
            fields_data (dict[str, Any], optional): The data to use in the SQL file.

        Returns:
            Optional[list[dict[str, Any]]]: The returned data if requested, else None.

        Raises:
            psycopg2.Error: If there is an error with the database.

        """
        with open(file_path, "r", encoding="utf-8") as sql_file:
            query = sql_file.read()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, fields_data)
                self.connection.commit()
                logging.info("Executed SQL file: %s", file_path)

                if not is_return_data:
                    return None

                column_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

        except psycopg2.Error as err:
            self.connection.rollback()
            logging.error("Database error: %s, performed a rollback", err)
            raise

        return [dict(zip(column_names, row)) for row in rows]

    def create_tables(self):
        """Create tables in the PostgreSQL database by executing a SQL script."""
        self.execute_sql_file(file_path="sql/create_tables.sql", is_return_data=False)

    # Website Info Operations

    def insert_website_data(self, fields_data: dict, is_return_data: bool = False):
        """Insert website data into the database."""
        self.execute_sql_file(
            file_path="sql/insert_website_info.sql",
            fields_data=fields_data,
            is_return_data=is_return_data,
        )

    def update_website_data(self, fields_data: dict):
        """Update website data in the database."""
        self.execute_sql_file(
            file_path="sql/update_website_info.sql",
            fields_data=fields_data,
            is_return_data=False,
        )

    def get_website_data(self, url: str = None):
        """Get website data from the database.

        Args:
            url (str, optional): The URL of the website. If None, gets all websites.

        """
        if not url:
            return self.execute_sql_file(
                file_path="sql/get_all_websites_info.sql",
                is_return_data=True,
            )

        return self.execute_sql_file(
            file_path="sql/get_website_info.sql",
            fields_data={"url": url},
            is_return_data=True,
        )

    # Website Monitoring Operations

    def batch_insert_monitoring_data(
        self, monitoring_data: list["WebsiteMonitoringResult"]
    ) -> None:
        """Insert a batch of website monitoring data into the database.

        Args:
            monitoring_data (list["WebsiteMonitoringResult"]): The monitoring data.

        Raises:
            psycopg2.Error: If there is an error with the database.

        """
        file_path = "sql/insert_website_monitoring_data.sql"
        with open(file_path, "r", encoding="utf-8") as sql_file:
            query = sql_file.read()

        processed_data = [
            asdict(monitoring_result) for monitoring_result in monitoring_data
        ]
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, processed_data)
            self.connection.commit()
            cursor.close()
        except psycopg2.Error as err:
            self.connection.rollback()
            logging.error("Database error: %s, performed a rollback", err)
            raise
