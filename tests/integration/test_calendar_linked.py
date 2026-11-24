"""Regression tests for linked calendar event writes."""
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from custom_components.home_tasks.calendar import HomeTasksCalendarEntity
from homeassistant.exceptions import ServiceValidationError


@pytest.mark.integration
async def test_create_linked_all_day_event(mock_config_entry, store):
    entity = HomeTasksCalendarEntity(mock_config_entry, store)
    await entity.async_create_event(
        summary="Dentist", description="Bring forms",
        dtstart=date(2027, 3, 12), dtend=date(2027, 3, 13),
    )
    task = next(t for t in store.tasks if t["title"] == "Dentist")
    assert task["due_date"] == "2027-03-12"
    assert task["due_time"] is None
    assert task["notes"] == "Bring forms"


@pytest.mark.integration
async def test_create_linked_timed_event(mock_config_entry, store):
    entity = HomeTasksCalendarEntity(mock_config_entry, store)
    await entity.async_create_event(
        summary="Meeting",
        start=datetime(2027, 3, 12, 14, 30, tzinfo=timezone.utc),
        end=datetime(2027, 3, 12, 15, 30, tzinfo=timezone.utc),
    )
    task = next(t for t in store.tasks if t["title"] == "Meeting")
    assert task["due_date"] is not None
    assert task["due_time"] is not None


@pytest.mark.integration
async def test_update_and_delete_linked_event(mock_config_entry, store):
    entity = HomeTasksCalendarEntity(mock_config_entry, store)
    task = await store.async_add_task("Original", due_date="2027-03-12")
    await entity.async_update_event(
        task["id"], {"summary": "Revised", "description": "Updated",
        "dtstart": date(2027, 3, 15), "dtend": date(2027, 3, 16)},
    )
    updated = store.get_task(task["id"])
    assert updated["title"] == "Revised"
    assert updated["notes"] == "Updated"
    assert updated["due_date"] == "2027-03-15"
    await entity.async_delete_event(task["id"])
    assert not any(t["id"] == task["id"] for t in store.tasks)


@pytest.mark.integration
async def test_invalid_event_does_not_create_task(mock_config_entry, store):
    entity = HomeTasksCalendarEntity(mock_config_entry, store)
    before = len(store.tasks)
    with pytest.raises(ServiceValidationError):
        await entity.async_create_event(
            summary="Invalid",
            start=date(2027, 3, 12), end=date(2027, 3, 11),
        )
    assert len(store.tasks) == before


@pytest.mark.integration
async def test_recurrence_instance_delete_is_rejected(mock_config_entry, store):
    entity = HomeTasksCalendarEntity(mock_config_entry, store)
    task = await store.async_add_task("Recurring", due_date="2027-03-12")
    with pytest.raises(ServiceValidationError):
        await entity.async_delete_event(task["id"], recurrence_id="2027-03-12")
    assert store.get_task(task["id"])
