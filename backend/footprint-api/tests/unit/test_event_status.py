from app.methodology.event_status import compute_event_status


def test_all_ok_is_measured():
    assert compute_event_status("ok", "ok", "ok") == "measured"


def test_mixed_ok_and_insufficient_is_partial():
    assert compute_event_status("ok", "insufficient_data", "ok") == "partial"


def test_all_insufficient_is_insufficient_data():
    assert compute_event_status("insufficient_data", "insufficient_data", "insufficient_data") == (
        "insufficient_data"
    )


def test_any_partial_counts_as_partial():
    assert compute_event_status("ok", "partial", "ok") == "partial"
