from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


DEFAULT_POSITION_ENDPOINTS = (
    "/current_position",
    "/satellite/current_position",
    "/api/current_position",
    "/position",
)

DEFAULT_SENTINEL_ENDPOINTS = (
    "/sentinel-2/image",
    "/sentinel2/image",
    "/api/sentinel-2/image",
    "/api/sentinel2/image",
    "/image/sentinel-2",
)


class SimSatError(RuntimeError):
    pass


class SimSatUnavailable(SimSatError):
    pass


@dataclass(frozen=True)
class SimSatResponse:
    endpoint: str
    url: str
    content_type: str
    body: bytes


class SimSatClient:
    def __init__(self, base_url: str = "http://localhost:9005", timeout_seconds: float = 10.0):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds

    def get_current_position(self, endpoints: Iterable[str] = DEFAULT_POSITION_ENDPOINTS) -> dict:
        response = self._get_first(endpoints, {})
        try:
            return json.loads(response.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SimSatError(f"Position endpoint did not return JSON: {response.url}") from exc

    def fetch_sentinel_tile(
        self,
        latitude: float,
        longitude: float,
        width: int = 512,
        height: int = 512,
        endpoints: Iterable[str] = DEFAULT_SENTINEL_ENDPOINTS,
    ) -> SimSatResponse:
        params = {
            "lat": f"{latitude:.6f}",
            "lon": f"{longitude:.6f}",
            "latitude": f"{latitude:.6f}",
            "longitude": f"{longitude:.6f}",
            "width": str(width),
            "height": str(height),
        }
        return self._get_first(endpoints, params)

    def _get_first(self, endpoints: Iterable[str], params: dict[str, str]) -> SimSatResponse:
        errors: list[str] = []
        for endpoint in endpoints:
            path = endpoint.lstrip("/")
            query = f"?{urlencode(params)}" if params else ""
            url = urljoin(self.base_url, path) + query
            request = Request(url, headers={"User-Agent": "kilnwatch-ingestion/0.1"})
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read()
                    content_type = response.headers.get("content-type", "application/octet-stream")
                    return SimSatResponse(endpoint="/" + path, url=url, content_type=content_type, body=body)
            except HTTPError as exc:
                errors.append(f"{url} -> HTTP {exc.code}")
            except URLError as exc:
                errors.append(f"{url} -> {exc.reason}")
            except TimeoutError:
                errors.append(f"{url} -> timed out")
        raise SimSatUnavailable("No SimSat endpoint responded successfully: " + "; ".join(errors))

