# -*- coding: utf-8 -*-
"""Website Monitor Module.

This module is used for monitoring websites. It periodically checks the availability of the websites
and stores the results in the database.

Todo:
    * Enhance error handling and retry logic
"""

import asyncio
import collections
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus

import aiohttp

from src.database_manager import DatabaseManager
from src.settings import MonitoringSettings

logger = logging.getLogger(__name__)


@dataclass
class WebsiteMonitoringResult:
    """Data class for storing website monitoring results.

    Attributes:
        request_timestamp (datetime): Timestamp when the request was sent.
        response_timestamp (datetime): Timestamp when the response was received.
        response_time (float): Time taken to receive the response.
        http_status_code (int): HTTP status code of the response.
        url (str, optional): URL of the website.
        website_id (int, optional): ID of the website in the database.
        is_regex_pattern_compliant (bool, optional): If regexp_pattern is given, whether the response complies with it.
    """

    request_timestamp: datetime
    response_timestamp: datetime
    response_time: float
    http_status_code: int
    url: str | None = None
    website_id: int | None = None
    is_regex_pattern_compliant: bool | None = None


class WebsiteMonitor:
    """Class for monitoring websites.

    Attributes:
        monitoring_results (collections.deque): Collection for storing monitoring results.
        db_manager (DatabaseManager): Database manager.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.monitoring_results = collections.deque()
        self.db_manager = db_manager

    async def check_website_recurrently(self, website_data: dict) -> None:
        """Monitors a website at a given interval.

        Args:
            website_data (dict): Website data including url, id and interval.
        """
        if not website_data["interval"]:
            logger.info(
                "Website %s has no interval specified, skip monitoring",
                website_data["url"],
            )
            return

        while True:
            url_monitoring_result = await check_website_availability(
                website_data["url"], website_data["regexp_pattern"]
            )
            url_monitoring_result.url = website_data["url"]
            url_monitoring_result.website_id = website_data["id"]
            self.monitoring_results.append(url_monitoring_result)
            await asyncio.sleep(website_data["interval"])

    async def launch_website_monitoring(self, website_data: dict) -> None:
        """Launches website monitoring as a separate task.

        Args:
            website_data (dict): Website data including url, id and interval.
        """
        asyncio.create_task(
            self.check_website_recurrently(website_data=website_data),
            name=website_data["url"],
        )

    async def monitor_websites(self, websites_data: list[dict]) -> None:
        """Monitors multiple websites.

        Args:
            websites_data (list[dict]): List of website data.
        """
        for website_data in websites_data:
            await self.launch_website_monitoring(website_data)

        while True:
            tasks = asyncio.all_tasks()
            logger.debug("Num of async tasks: %s", len(tasks))
            while not self.monitoring_results:
                await asyncio.sleep(MonitoringSettings.RESULTS_WORKER_WAIT_TIME)

            try:
                self.save_website_monitoring_results()
            except Exception as err:
                logger.error("Could not save the websites, err: %s", err)

    def save_website_monitoring_results(self) -> None:
        """Saves website monitoring results to the database."""
        monitoring_data = []
        http_status_code_to_counter = collections.defaultdict(int)
        processed_results_num = 0
        while (
            self.monitoring_results
            and processed_results_num < MonitoringSettings.RESULTS_BATCH_SAVE_SIZE
        ):
            url_monitoring_result = self.monitoring_results.popleft()
            monitoring_data.append(url_monitoring_result)
            http_status_code_to_counter[url_monitoring_result.http_status_code] += 1
            processed_results_num += 1

        self.db_manager.batch_insert_monitoring_data(monitoring_data)
        sorted_http_status_to_code = dict(
            sorted(
                http_status_code_to_counter.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        logger.info(
            "Saved %s websites, http status codes breakdown: %s",
            len(monitoring_data),
            sorted_http_status_to_code,
        )


async def check_website_availability(
    url: str, regexp_pattern: str = None
) -> WebsiteMonitoringResult:
    """Checks the availability of a website.

    Args:
        url (str): Website URL to check.
        regexp_pattern (str, optional): Optional regular expression pattern to check in the response.

    Returns:
        WebsiteMonitoringResult: Result of the website check.
    """
    async with aiohttp.ClientSession() as session:
        for scheme in ("https", "http"):
            target_url = scheme + "://" + url
            request_timestamp = datetime.now()
            is_regex_pattern_compliant = None
            try:
                if not regexp_pattern:
                    response = await session.head(
                        target_url,
                        allow_redirects=True,
                        timeout=MonitoringSettings.REQUEST_TIMEOUT,
                    )
                else:
                    response = await session.get(
                        target_url,
                        allow_redirects=True,
                        timeout=MonitoringSettings.REQUEST_TIMEOUT,
                    )
                    response_body = await response.text()
                    is_regex_pattern_compliant = (
                        re.search(regexp_pattern, response_body) is not None
                    )

                response_timestamp = datetime.now()
                response_time = (response_timestamp - request_timestamp).total_seconds()
                http_status_code = response.status
            except asyncio.exceptions.TimeoutError:
                response_timestamp = datetime.now()
                response_time = MonitoringSettings.REQUEST_TIMEOUT
                http_status_code = HTTPStatus.REQUEST_TIMEOUT.value
            except aiohttp.ClientError as err:
                logger.error("Error connecting to website %s: %s", url, err)
                raise

            return WebsiteMonitoringResult(
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                response_time=response_time,
                http_status_code=http_status_code,
                is_regex_pattern_compliant=is_regex_pattern_compliant,
            )
