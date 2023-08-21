CREATE TABLE IF NOT EXISTS websites_info (
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) UNIQUE NOT NULL,
    interval INT,
    regexp_pattern VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS monitoring_results (
    id SERIAL PRIMARY KEY,
    website_id INT NOT NULL,
    request_timestamp TIMESTAMPTZ NOT NULL,
    response_timestamp TIMESTAMPTZ NOT NULL,
    response_time FLOAT NOT NULL,
    http_status_code INT NOT NULL,
    is_regex_pattern_compliant BOOL,
    CONSTRAINT fk_website
        FOREIGN KEY (website_id)
        REFERENCES websites_info (id)
        ON DELETE CASCADE
);