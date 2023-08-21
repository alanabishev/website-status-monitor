INSERT INTO websites_info (url, interval, regexp_pattern)
VALUES (%(url)s, %(interval)s, %(regexp_pattern)s)
RETURNING id;