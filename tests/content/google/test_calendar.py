"""content/google/calendar.py の単体テスト。"""

from __future__ import annotations

from google_ical.content.google.calendar import list_managed_events, upsert_event


class _FakeListRequest:
    def __init__(self, *, responses: list[dict[str, object]], service: "_FakeEventsResource") -> None:
        self._responses = responses
        self._index = 0
        self._service = service
        self._kwargs: dict[str, object] = {}

    def execute(self) -> dict[str, object]:
        return self._responses[self._index]

    @property
    def kwargs(self) -> dict[str, object]:
        return self._kwargs


class _FakeEventsResource:
    def __init__(self, *, responses_by_source: dict[str, list[dict[str, object]]]) -> None:
        self.responses_by_source = responses_by_source
        self.insert_calls: list[dict[str, object]] = []
        self.update_calls: list[dict[str, object]] = []
        self.delete_calls: list[str] = []

    def list(self, **kwargs: object) -> _FakeListRequest:
        source = _source_from_filter(kwargs.get("privateExtendedProperty"))
        request = _FakeListRequest(responses=self.responses_by_source.get(source, [{"items": []}]), service=self)
        request._kwargs = kwargs
        return request

    def list_next(self, request: _FakeListRequest, response: dict[str, object]) -> _FakeListRequest | None:
        if request._index + 1 < len(request._responses):
            request._index += 1
            return request
        return None

    def insert(self, **kwargs: object) -> "_FakeMutationRequest":
        self.insert_calls.append(kwargs)
        return _FakeMutationRequest({"id": "new-google-id"})

    def update(self, **kwargs: object) -> "_FakeMutationRequest":
        self.update_calls.append(kwargs)
        return _FakeMutationRequest({"id": kwargs["eventId"]})

    def delete(self, **kwargs: object) -> "_FakeMutationRequest":
        self.delete_calls.append(str(kwargs["eventId"]))
        return _FakeMutationRequest({})


class _FakeMutationRequest:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def execute(self) -> dict[str, object]:
        return self.payload


class _FakeService:
    def __init__(self, events_resource: _FakeEventsResource) -> None:
        self._events = events_resource

    def events(self) -> _FakeEventsResource:
        return self._events


def _source_from_filter(value: object) -> str:
    assert isinstance(value, str)
    return value.split("=", 1)[1]


def test_list_managed_events_filters_by_private_extended_property() -> None:
    service = _FakeService(
        _FakeEventsResource(
            responses_by_source={
                "gomi": [
                    {
                        "items": [
                            {
                                "id": "google-1",
                                "extendedProperties": {
                                    "private": {
                                        "google_ical_id": "hash-1",
                                        "google_ical_source": "gomi",
                                    },
                                },
                            },
                            {
                                "id": "google-2",
                                "extendedProperties": {
                                    "private": {
                                        "google_ical_id": "hash-2",
                                        "google_ical_source": "manual",
                                    },
                                },
                            },
                        ],
                    },
                ],
                "manual": [
                    {
                        "items": [
                            {
                                "id": "google-3",
                                "extendedProperties": {
                                    "private": {
                                        "google_ical_id": "hash-3",
                                        "google_ical_source": "manual",
                                    },
                                },
                            },
                        ],
                    },
                ],
            },
        ),
    )

    managed = list_managed_events(service, calendar_id="cal-id", sources=("gomi", "manual"))

    assert set(managed) == {"hash-1", "hash-3"}
    assert managed["hash-1"]["id"] == "google-1"
    assert managed["hash-3"]["id"] == "google-3"


def test_upsert_event_inserts_when_missing() -> None:
    events = _FakeEventsResource(responses_by_source={})
    service = _FakeService(events)

    google_id = upsert_event(
        service,
        calendar_id="cal-id",
        body={"summary": "可燃ごみ"},
        existing=None,
    )

    assert google_id == "new-google-id"
    assert len(events.insert_calls) == 1
    assert events.update_calls == []


def test_upsert_event_updates_when_existing() -> None:
    events = _FakeEventsResource(responses_by_source={})
    service = _FakeService(events)

    google_id = upsert_event(
        service,
        calendar_id="cal-id",
        body={"summary": "可燃ごみ"},
        existing={"id": "google-1"},
    )

    assert google_id == "google-1"
    assert len(events.update_calls) == 1
    assert events.insert_calls == []
