from __future__ import annotations

from yaaf.responses import Response, as_response


def test_as_response_string() -> None:
    response = as_response("hello")
    assert response.body == b"hello"
    assert response.status == 200


def test_as_response_bytes() -> None:
    response = as_response(b"data")
    assert response.body == b"data"
    assert response.status == 200


def test_as_response_dict_json() -> None:
    response = as_response({"ok": True})
    assert response.status == 200
    assert b"\"ok\"" in response.body


def test_as_response_tuple_status() -> None:
    response = as_response(("nope", 404))
    assert response.status == 404
    assert response.body == b"nope"


def test_response_with_status() -> None:
    base = Response.text("hi")
    updated = base.with_status(201)
    assert updated.status == 201
    assert updated.body == base.body
