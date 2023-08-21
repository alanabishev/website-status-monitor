UPDATE websites_info
SET interval = %(interval)s, regexp_pattern = %(regexp_pattern)s
WHERE id = %(id)s;