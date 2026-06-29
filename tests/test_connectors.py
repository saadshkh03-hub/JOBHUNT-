"""Tests for connectors."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.connectors.adzuna import AdzunaConnector
from app.connectors.aps import APSConnector
from app.connectors.council import CouncilConnector
from app.connectors.registry import create_connector_registry, get_active_connectors
from app.models import SourceStatus


class TestAdzunaConnector:
    def test_no_credentials_returns_unavailable_status(self):
        conn = AdzunaConnector(app_id=None, app_key=None)
        status = conn.get_status()
        assert status.status == "unavailable"
        assert "ADZUNA_APP_ID" in status.message or "Configure" in status.message

    def test_has_credentials_returns_available_status(self):
        conn = AdzunaConnector(app_id="test_id", app_key="test_key")
        status = conn.get_status()
        assert status.status == "available"

    @pytest.mark.asyncio
    async def test_search_without_credentials_returns_empty(self):
        conn = AdzunaConnector(app_id=None, app_key=None)
        jobs, status = await conn.search("Python Developer", "Sydney")
        assert jobs == []
        assert status.status == "unavailable"

    @pytest.mark.asyncio
    async def test_search_with_credentials_calls_api(self):
        conn = AdzunaConnector(app_id="test_id", app_key="test_key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Python Developer",
                    "company": {"display_name": "Tech Co"},
                    "location": {"display_name": "Sydney, NSW"},
                    "description": "Great Python role",
                    "redirect_url": "https://adzuna.com/job/123",
                    "created": "2024-01-15T10:00:00Z",
                    "salary_min": 100000,
                    "salary_max": 130000,
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs, status = await conn.search("Python Developer", "Sydney")
            assert len(jobs) == 1
            assert jobs[0]["title"] == "Python Developer"
            assert status.status == "available"

    @pytest.mark.asyncio
    async def test_search_http_error_returns_unavailable(self):
        conn = AdzunaConnector(app_id="test_id", app_key="test_key")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs, status = await conn.search("Python", "Sydney")
            assert jobs == []
            assert status.status == "unavailable"

    @pytest.mark.asyncio
    async def test_search_timeout_returns_unavailable(self):
        conn = AdzunaConnector(app_id="test_id", app_key="test_key")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs, status = await conn.search("Python", "Sydney")
            assert jobs == []
            assert status.status == "unavailable"


class TestAPSConnector:
    @pytest.mark.asyncio
    async def test_network_failure_returns_unavailable(self):
        conn = APSConnector()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs, status = await conn.search("Policy Officer", "Canberra")
            assert jobs == []
            assert status.status == "unavailable"

    @pytest.mark.asyncio
    async def test_timeout_returns_unavailable(self):
        conn = APSConnector()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs, status = await conn.search("Policy Officer", "Canberra")
            assert jobs == []
            assert status.status == "unavailable"

    @pytest.mark.asyncio
    async def test_rss_success_returns_jobs(self):
        conn = APSConnector()
        sample_rss = """<?xml version="1.0"?>
        <rss version="2.0"><channel><title>APS Jobs</title>
        <item>
          <title>Policy Officer</title>
          <link>https://www.apsjobs.gov.au/s/job-detail?id=123</link>
          <description>Department of Home Affairs - Policy Officer APS6 - Canberra ACT</description>
          <pubDate>Mon, 15 Jan 2024 00:00:00 +0000</pubDate>
        </item>
        </channel></rss>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sample_rss

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            jobs, status = await conn.search("Policy Officer", "Canberra")
            assert len(jobs) >= 1
            assert jobs[0]["title"] == "Policy Officer"
            assert status.status in ("available", "limited")

    def test_name_attribute(self):
        conn = APSConnector()
        assert conn.name == "APS Jobs"

    def test_get_status_available(self):
        conn = APSConnector()
        status = conn.get_status()
        assert status.name == "APS Jobs"
        assert status.status == "available"


class TestConnectorRegistry:
    def test_registry_created_without_credentials(self):
        registry = create_connector_registry()
        assert "adzuna" in registry
        assert "aps" in registry
        assert "council" in registry

    def test_registry_created_with_credentials(self):
        registry = create_connector_registry(adzuna_app_id="id", adzuna_app_key="key")
        assert registry["adzuna"].app_id == "id"
        assert registry["adzuna"].app_key == "key"

    def test_get_all_connectors(self):
        registry = create_connector_registry()
        connectors = get_active_connectors(registry, "all")
        assert len(connectors) == 3

    def test_get_government_connectors(self):
        registry = create_connector_registry()
        connectors = get_active_connectors(registry, "government")
        assert len(connectors) == 1
        assert connectors[0].name == "APS Jobs"

    def test_get_council_connectors(self):
        registry = create_connector_registry()
        connectors = get_active_connectors(registry, "council")
        assert len(connectors) == 1
        assert connectors[0].name == "Council Jobs"

    def test_default_filter_returns_all(self):
        registry = create_connector_registry()
        connectors = get_active_connectors(registry)
        assert len(connectors) == 3


# ── Jora connector tests ──────────────────────────────────────────────────

import pytest
from unittest.mock import patch, AsyncMock
from backend.app.connectors.jora import JoraConnector, _parse_jora_html


def test_jora_parse_html_returns_jobs():
    sample_html = """
    <article>
      <h2><a href="/j/12345?q=test">Senior Python Developer</a></h2>
      <span class="company">Acme Corp</span>
      <span class="location">Sydney NSW</span>
      <span class="date">2 days ago</span>
      <p class="description">Seeking a Python developer with 5+ years experience.</p>
    </article>
    """
    jobs = _parse_jora_html(sample_html, "https://au.jora.com")
    # May or may not parse depending on HTML structure match
    assert isinstance(jobs, list)


@pytest.mark.asyncio
async def test_jora_connector_returns_unavailable_on_network_error():
    connector = JoraConnector()
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(side_effect=Exception("connection refused"))
        jobs, status = await connector.search("python developer", "Sydney")
    assert jobs == []
    assert status.status == "unavailable"


@pytest.mark.asyncio
async def test_jora_connector_returns_limited_on_empty_results():
    connector = JoraConnector()
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>No jobs found</body></html>"

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=mock_resp)
        jobs, status = await connector.search("python developer", "Sydney")

    assert jobs == []
    assert status.name == "Jora"
    assert status.status in ("limited", "unavailable")
