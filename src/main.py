# -*- coding: utf-8 -*-
"""Website Monitoring API.

This module provides a FastAPI-based API for managing website monitoring information.
It allows creating and updating website information, which includes the URL, monitoring
interval, and regular expression pattern to match specific content on the website.

Example:
    To start the application, run the following command:
        $ python main.py

    You can then access the API documentation and interact with the endpoints through the Swagger UI.

Attributes:
    app (FastAPI): The FastAPI application instance used for routing requests.
    logger (logging.Logger): The logger instance for logging messages.

"""

import asyncio
import logging
from functools import wraps
from http import HTTPStatus

from fastapi import FastAPI, HTTPException
from pydantic import Extra
from pydantic.main import BaseModel

from src.settings import MonitoringSettings
from src.database_manager import DatabaseManager
from src.url_validator import get_formatted_url, InvalidUrlException
from src.website_monitor import WebsiteMonitor

app = FastAPI()
logger = logging.getLogger(__name__)


class WebsiteInfo(BaseModel):
    """Data model representing website information."""

    url: str
    interval: int | None = None
    regexp_pattern: str | None = None

    class Config:
        extra = Extra.forbid


def validate_and_alter_website_info_url(func):
    """Decorator function to validate and change the url of the `WebsiteInfo` object.

    This decorator validates the URL in the `WebsiteInfo` object by calling the `get_formatted_url`
    function from the `url_validator` module. If the URL is invalid, it raises an `HTTPException`
    with a status code of `HTTPStatus.BAD_REQUEST`.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The decorated function.

    Raises:
        HTTPException: If the URL in the `WebsiteInfo` object is invalid.

    """

    @wraps(func)
    async def wrapper(website_info: WebsiteInfo, *args, **kwargs):
        try:
            website_info.url = get_formatted_url(website_info.url)
        except InvalidUrlException as err:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST.value,
                detail=f"Invalid URL: {website_info.url}",
            ) from err

        return await func(website_info, *args, **kwargs)

    return wrapper


@app.on_event("startup")
async def startup_event():
    """Event handler called on application startup.

    Initializes the database manager, creates necessary tables,
    retrieves website data, and starts the website monitor task.

    """
    db_manager = DatabaseManager()
    db_manager.check_db()
    db_manager.create_tables()

    websites = db_manager.get_website_data()
    website_monitor = WebsiteMonitor(db_manager)
    asyncio.create_task(website_monitor.monitor_websites(websites))
    app.state.website_monitor = website_monitor
    app.state.db_manager = db_manager


@app.post("/create_website_info", status_code=HTTPStatus.CREATED.value)
@validate_and_alter_website_info_url
async def create_website_info(website_info: WebsiteInfo):
    """Create website information.

    Creates new website information in the database, and starts monitoring
    the website using the website monitor.

    Args:
        website_info (WebsiteInfo): The website information to create.

    Returns:
        dict: A response message indicating the success of the operation.

    Raises:
        HTTPException: If a website with the same URL already exists.

    """
    found_website = app.state.db_manager.get_website_data(url=website_info.url)
    if found_website:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.value,
            detail=f"Website with URL {website_info.url} already exists",
        )

    website_info_data = website_info.dict()
    app.state.db_manager.insert_website_data(website_info_data)
    found_websites = app.state.db_manager.get_website_data(url=website_info.url)
    await app.state.website_monitor.launch_website_monitoring(found_websites[0])
    return {"message": "Website added to monitoring"}


@app.patch("/update_website_info", status_code=HTTPStatus.OK.value)
@validate_and_alter_website_info_url
async def update_website_info(website_info: WebsiteInfo):
    """Update website information.

    Updates the website information in the database based on the provided
    website URL. The interval and regular expression pattern can be modified.

    Args:
        website_info (WebsiteInfo): The website information to update.

    Returns:
        dict: A response message indicating the success of the operation.

    Raises:
        HTTPException: If the website with the provided URL is not found.

    """
    if website_info.interval is None and website_info.regexp_pattern is None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.value,
            detail="Interval or regexp_pattern should be filled",
        )

    found_websites = app.state.db_manager.get_website_data(url=website_info.url)
    if not found_websites:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND.value,
            detail=f"Website with URL {website_info.url} not found",
        )

    found_website = found_websites[0]
    if website_info.interval is not None:
        found_website["interval"] = website_info.interval

    if website_info.regexp_pattern is not None:
        found_website["regexp_pattern"] = website_info.regexp_pattern

    app.state.db_manager.update_website_data(fields_data=found_website)
    return {
        "message": "Website info changed, it will be applied during the next run of the app"
    }


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    )
    uvicorn.run(app, host="0.0.0.0", port=MonitoringSettings.UVICORN_PORT)
