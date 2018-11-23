from dateparser import parse

DATEPARSER_SETTING = {
    'TIMEZONE': 'UTC',
    'STRICT_PARSING': True
}

def parse_date(thedate):
    thedatetime = parse(thedate)
    if not thedatetime:
        return None
    return thedatetime.date()

def parse_datetime(thedate):
    return parse(thedate)
