"""Pytest fixtures for Workshop tests.

Provides isolated test environment with per-test database directories.
"""

import pytest
from pathlib import Path

from app import create_app
from app.services import incident_logger


@pytest.fixture
def client(tmp_path):
    """Flask test client with isolated incident database.

    Each test gets its own temporary data directory to ensure
    complete isolation of the incidents SQLite database.
    """
    # Set up isolated DB path for this test
    incident_logger.set_db_path(tmp_path / "incidents.db")

    application = create_app(start_health_loop=False, data_dir=tmp_path)
    application.config["TESTING"] = True

    with application.test_client() as client:
        yield client

    # Clean up after test
    incident_logger.set_db_path(None)


@pytest.fixture(autouse=True)
def clean_incidents():
    """Clear incident database before and after each test."""
    incident_logger.clear_all()
    yield
    incident_logger.clear_all()
