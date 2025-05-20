# test_event_log.py
from services.event_log import append_event, get_recent_events
from scheduler.gas_fetcher import iso_utc

append_event(5, "above", iso_utc())
append_event(2, "below", iso_utc())

print(get_recent_events())
