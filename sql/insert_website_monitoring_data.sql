INSERT INTO monitoring_results (
    website_id,
    request_timestamp,
    response_timestamp,
    response_time,
    http_status_code,
    is_regex_pattern_compliant
)
VALUES (
    %(website_id)s,
    %(request_timestamp)s,
    %(response_timestamp)s,
    %(response_time)s,
    %(http_status_code)s,
    %(is_regex_pattern_compliant)s
)
RETURNING id;
