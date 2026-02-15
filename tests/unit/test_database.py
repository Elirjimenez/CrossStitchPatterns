"""Tests for database connection factory functions."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.database import (
    Base,
    build_engine,
    build_session_factory,
)


class TestBase:
    """Tests for Base declarative class."""

    def test_base_is_declarative_base(self):
        """Base should be a SQLAlchemy declarative base."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestBuildEngine:
    """Tests for build_engine function."""

    def test_returns_engine_for_sqlite(self):
        """Should create engine for SQLite in-memory database."""
        engine = build_engine("sqlite:///:memory:")

        assert engine is not None
        assert str(engine.url) == "sqlite:///:memory:"

    def test_returns_engine_for_postgresql(self):
        """Should create engine for PostgreSQL URL."""
        # Note: doesn't actually connect, just creates engine object
        url = "postgresql://user:pass@localhost/dbname"
        engine = build_engine(url)

        assert engine is not None
        assert "postgresql" in str(engine.url)

    def test_echo_is_disabled(self):
        """Should create engine with echo=False."""
        engine = build_engine("sqlite:///:memory:")

        # echo is stored in engine.echo
        assert engine.echo is False


class TestBuildSessionFactory:
    """Tests for build_session_factory function."""

    def test_returns_sessionmaker(self):
        """Should return a sessionmaker instance."""
        factory = build_session_factory("sqlite:///:memory:")

        assert isinstance(factory, sessionmaker)

    def test_creates_working_sessions(self):
        """Should create sessions that can execute queries."""
        factory = build_session_factory("sqlite:///:memory:")
        session = factory()

        try:
            # Should be able to execute a simple query
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        finally:
            session.close()

    def test_sessions_bound_to_engine(self):
        """Should create sessions bound to the engine."""
        factory = build_session_factory("sqlite:///:memory:")

        # Factory should have bind attribute set
        assert factory.kw.get("bind") is not None

    def test_multiple_sessions_from_same_factory(self):
        """Should be able to create multiple sessions from same factory."""
        factory = build_session_factory("sqlite:///:memory:")

        session1 = factory()
        session2 = factory()

        try:
            assert session1 is not session2
            assert session1 is not None
            assert session2 is not None
        finally:
            session1.close()
            session2.close()
