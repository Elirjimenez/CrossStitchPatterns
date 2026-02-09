from app.config import Settings, get_settings


def test_settings_loads_with_defaults():
    """Settings can be created without .env file."""
    s = Settings()
    assert s.database_url == "postgresql://user:pass@localhost:5432/crossstitch"
    assert s.default_aida_count == 14
    assert s.max_pattern_size == 500
    assert s.app_version == "0.1.0"


def test_get_settings_returns_settings_instance():
    s = get_settings()
    assert isinstance(s, Settings)


def test_get_settings_has_app_version():
    s = get_settings()
    assert s.app_version == "0.1.0"
