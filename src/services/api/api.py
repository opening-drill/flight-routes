import json
from urllib import error, request

from src.config import (
    get_api_key,
    get_api_key_header_name,
    get_api_login_password,
    get_api_login_url,
    get_api_login_username,
    get_dispatch_timeout_seconds,
    get_dispatch_url,
)
from src.config.constants import CONTENT_TYPE_JSON


def dispatch_simulation_payloads(
    payloads: dict[str, object] | list[dict[str, object]],
    dispatch_url: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, object] | list[dict[str, object]]:
    resolved_dispatch_url = dispatch_url or get_dispatch_url()
    resolved_timeout_seconds = timeout_seconds or get_dispatch_timeout_seconds()
    auth_headers = build_authenticated_headers(
        timeout_seconds=resolved_timeout_seconds,
    )
    payload_list = payloads if isinstance(payloads, list) else [payloads]

    responses = [
        post_json(
            url=resolved_dispatch_url,
            payload=payload,
            timeout_seconds=resolved_timeout_seconds,
            extra_headers=auth_headers,
        )
        for payload in payload_list
    ]

    if isinstance(payloads, list):
        return responses

    return responses[0]


def build_authenticated_headers(timeout_seconds: float) -> dict[str, str]:
    auth_headers = build_optional_api_key_headers()
    login_response = post_json(
        url=get_api_login_url(),
        payload={
            "username": get_api_login_username(),
            "password": get_api_login_password(),
        },
        timeout_seconds=timeout_seconds,
        extra_headers=auth_headers,
    )
    token = login_response.get("token")

    if not isinstance(token, str) or not token.strip():
        raise ValueError("API login succeeded but no token was returned.")

    auth_headers["Authorization"] = f"Bearer {token}"
    return auth_headers


def build_optional_api_key_headers() -> dict[str, str]:
    api_key = get_api_key()
    if not api_key:
        return {}
    return {get_api_key_header_name(): api_key}


def post_json(
    url: str,
    payload: dict[str, object],
    timeout_seconds: float,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, object]:
    request_body = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": CONTENT_TYPE_JSON}

    if extra_headers:
        request_headers.update(extra_headers)

    http_request = request.Request(
        url=url,
        data=request_body,
        headers=request_headers,
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"API request failed with status {exc.code} at {url}: {error_body}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach API endpoint {url}: {exc.reason}") from exc

    if not response_body:
        return {"success": True}

    try:
        return json.loads(response_body)
    except json.JSONDecodeError:
        return {"success": True, "raw_response": response_body}
