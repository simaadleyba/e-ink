#!/usr/bin/env python3
"""Apple Reminders provider via CalDAV."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import List, Optional, Union

from caldav import DAVClient
from icalendar import Calendar


@dataclass(frozen=True)
class ReminderItem:
    summary: str
    due: Optional[datetime]
    completed: bool


class RemindersProvider:
    """Fetch reminders from Apple Reminders via CalDAV."""

    def __init__(self, config: dict):
        reminders_config = config.get("reminders", {})
        self.username = reminders_config.get("username")
        self.app_password = reminders_config.get("app_password")
        self.caldav_url = reminders_config.get("caldav_url")
        self.list_name = reminders_config.get("list_name", "Reminders")
        self.max_items = int(reminders_config.get("max_items", 8))
        self.show_completed = bool(reminders_config.get("show_completed", False))

        if not all([self.username, self.app_password, self.caldav_url]):
            missing = [
                key
                for key, value in (
                    ("username", self.username),
                    ("app_password", self.app_password),
                    ("caldav_url", self.caldav_url),
                )
                if not value
            ]
            raise ValueError(f"Missing reminders config values: {', '.join(missing)}")

    def _get_calendar(self):
        client = DAVClient(url=self.caldav_url, username=self.username, password=self.app_password)
        principal = client.principal()
        calendars = principal.calendars()
        for calendar in calendars:
            if calendar.name == self.list_name:
                return calendar
        return calendars[0] if calendars else None

    def _normalize_due(self, value: Union[datetime, date]) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.combine(value, time.min)

    def _parse_todo(self, todo_data: Union[bytes, str]) -> List[ReminderItem]:
        reminders: List[ReminderItem] = []
        calendar = Calendar.from_ical(todo_data)
        for component in calendar.walk():
            if component.name != "VTODO":
                continue
            summary = str(component.get("summary", "")).strip()
            status = str(component.get("status", "")).upper()
            completed = status == "COMPLETED" or component.get("completed") is not None
            due = None
            if component.get("due"):
                decoded_due = component.decoded("due")
                if isinstance(decoded_due, (datetime, date)):
                    due = self._normalize_due(decoded_due)
            reminders.append(ReminderItem(summary=summary, due=due, completed=completed))
        return reminders

    def fetch_reminders(self) -> List[ReminderItem]:
        calendar = self._get_calendar()
        if calendar is None:
            return []
        todos = calendar.todos(include_completed=self.show_completed)
        reminders: List[ReminderItem] = []
        for todo in todos:
            todo_data = getattr(todo, "data", None)
            if todo_data is None:
                todo_component = getattr(todo, "icalendar_component", None)
                if todo_component is not None:
                    todo_data = todo_component.to_ical()
            if not todo_data:
                continue
            reminders.extend(self._parse_todo(todo_data))

        if not self.show_completed:
            reminders = [item for item in reminders if not item.completed]

        reminders.sort(key=lambda item: (item.due is None, item.due or datetime.max))
        return reminders[: self.max_items]
