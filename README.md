# Website Monitor Project

This project implements a program that monitors the availability of multiple websites over the network. 
It collects various metrics about the websites and stores them into a PostgreSQL database. 
The monitoring process includes checking the request timestamp, response time, HTTP status code, 
and optionally verifying the returned page contents against a regular expression pattern.
The system uses asyncio, aiohttp for website availability check and psycopg2 for db interaction. 
FastApi was used for adding/editing website info.
Formatting is provided by black and linter used is pylint.

## Features

- Periodic website checks: The program performs periodic checks on the websites to monitor their availability. 
- New websites can be added via a http request, and are added to monitoring.
- Customizable intervals and regexp: The interval between checks and regexp pattern can be configured for each website
- Regular expression matching: Optionally, the program can check if the returned page contents match a specific regular expression pattern.
- Database storage: The monitoring results are stored in a PostgreSQL database.
- Tests coverage

## Setup

Follow the steps below to set up and run the website monitor program:

1) Clone the repository 
2) Run the script using
```
chmod +x runner.sh
./runner.sh
```
This will build image of the service and run it. It will prompt you to enter the db credentials for the service. 
3) To interact with the service, it exposes port 8000, so you can curl or use postman to interact using rest requests
4) To access the documentation, go to http://localhost:8000/docs, it contains 2 methods to add and change websites

Alternatively, you can run using python src/main.py, but make sure you install dependencies from pip


## Limitations/ Improvements

1) While the web checker is async, the db uses psycopg2 which is not async. 
I would need some more time to make db connection async using either asyncpg or psycopg3(in beta) 
2) Error handling for website availability. While the program handles some of the http errors, 
it depends on what to do when we encounter some errors. 
For example: should we retry the request? Should we not use ssl (safety)? 
For now if we encounter an error an asyncio task is dropped, with error logged and raised.
3) Split website monitoring results worker that writes to db and website monitor. They can communicate using
a queue of messages, which would help with scaling and error handling. 


## License

This project is licensed under the [MIT License](LICENSE).