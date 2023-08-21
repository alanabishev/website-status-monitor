import asyncio
import collections
from datetime import datetime
from http import HTTPStatus
from unittest.mock import AsyncMock, patch, Mock

import pytest
from aiohttp import ClientError

from src.website_monitor import (
    check_website_availability,
    WebsiteMonitoringResult,
    MonitoringSettings,
    WebsiteMonitor,
)


class TestWebsiteMonitor:
    def setup_method(self):
        self.tst_obj = WebsiteMonitor(
            db_manager=Mock(batch_insert_monitoring_data=Mock())
        )
        self.website_monitoring_result = WebsiteMonitoringResult(
            url="test.com",
            request_timestamp=datetime.now(),
            response_timestamp=datetime.now(),
            response_time=5,
            http_status_code=HTTPStatus.OK,
        )

    @pytest.mark.asyncio
    async def test_monitor_single_website(self):
        with patch(
            "src.website_monitor.check_website_availability", new_callable=AsyncMock
        ) as mocked_check:
            mocked_check.return_value = self.website_monitoring_result
            website_data = {
                "url": "www.test.com",
                "id": 1,
                "interval": 10,
                "regexp_pattern": None,
            }

            asyncio.create_task(self.tst_obj.check_website_recurrently(website_data))

            await asyncio.sleep(2.5)
            assert len(self.tst_obj.monitoring_results) == 1
            assert self.tst_obj.monitoring_results[0] == self.website_monitoring_result

    @pytest.mark.asyncio
    async def test_monitor_multiple_websites(self):
        with patch(
            "src.website_monitor.check_website_availability", new_callable=AsyncMock
        ) as mocked_check:
            mocked_check.return_value = self.website_monitoring_result
            db_manager_mock = Mock()
            monitor = WebsiteMonitor(db_manager=db_manager_mock)
            websites_data = [
                {
                    "url": "www.test1.com",
                    "id": 1,
                    "interval": 10,
                    "regexp_pattern": None,
                },
                {
                    "url": "www.test2.com",
                    "id": 2,
                    "interval": 10,
                    "regexp_pattern": None,
                },
            ]
            asyncio.create_task(monitor.monitor_websites(websites_data))
            await asyncio.sleep(2.5)
            assert len(monitor.monitoring_results) == 2

    @pytest.mark.asyncio
    async def test_save_website_monitoring_results(self):
        self.tst_obj.monitoring_results = collections.deque(
            [self.website_monitoring_result for _ in range(10)]
        )

        self.tst_obj.save_website_monitoring_results()

        self.tst_obj.db_manager.batch_insert_monitoring_data.assert_called_once()
        assert len(self.tst_obj.monitoring_results) == 0

    @pytest.mark.asyncio
    async def test_no_interval_skip_monitoring(self):
        db_manager_mock = Mock()
        monitor = WebsiteMonitor(db_manager=db_manager_mock)
        website_data = {
            "url": "www.test.com",
            "id": 1,
            "interval": 0,
            "regexp_pattern": None,
        }
        asyncio.create_task(monitor.check_website_recurrently(website_data))
        await asyncio.sleep(1)
        assert len(monitor.monitoring_results) == 0


@pytest.mark.asyncio
async def test_check_website_availability_no_regexp():
    url = "www.test.com"
    with patch("aiohttp.ClientSession.head", new_callable=AsyncMock) as mocked_head:
        mocked_head.return_value = AsyncMock(status=HTTPStatus.OK)
        result = await check_website_availability(url)
        assert isinstance(result, WebsiteMonitoringResult)
        assert result.http_status_code == HTTPStatus.OK
        assert result.is_regex_pattern_compliant is None


@pytest.mark.asyncio
async def test_check_website_availability_with_regexp():
    url = "www.test.com"
    regexp = "Test Pattern"
    with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mocked_get:
        mocked_get.return_value = AsyncMock(
            status=HTTPStatus.OK,
            text=AsyncMock(return_value="Test Pattern in response"),
        )
        result = await check_website_availability(url, regexp)
        assert isinstance(result, WebsiteMonitoringResult)
        assert result.http_status_code == HTTPStatus.OK
        assert result.is_regex_pattern_compliant is True


@pytest.mark.asyncio
async def test_check_website_availability_timeout():
    url = "www.test.com"
    with patch("aiohttp.ClientSession.head", new_callable=AsyncMock) as mocked_head:
        mocked_head.side_effect = asyncio.exceptions.TimeoutError
        result = await check_website_availability(url)
        assert isinstance(result, WebsiteMonitoringResult)
        assert result.http_status_code == HTTPStatus.REQUEST_TIMEOUT
        assert result.response_time == MonitoringSettings.REQUEST_TIMEOUT


@pytest.mark.asyncio
async def test_check_website_availability_client_error():
    url = "www.test.com"
    with patch("aiohttp.ClientSession.head", new_callable=AsyncMock) as mocked_head:
        mocked_head.side_effect = ClientError()
        with pytest.raises(ClientError):
            await check_website_availability(url)
