from minimal_fastapi_app.core.config import Settings


def test_default_settings():
    """Test default settings values"""
    settings = Settings()
    assert settings.app_name == "Minimal FastAPI App"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.environment == "development"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_settings_from_env(monkeypatch):
    """Test settings can be overridden by environment variables"""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 32)  # Set a valid secret key for production

    settings = Settings()
    assert settings.app_name == "Test App"
    assert settings.debug is True
    assert settings.port == 9000
    assert settings.environment == "production"


def test_case_insensitive_env_vars(monkeypatch):
    """Test that environment variables are case insensitive"""
    monkeypatch.setenv("app_name", "Case Test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")  # Use uppercase for Literal validation

    settings = Settings()
    assert settings.app_name == "Case Test"
    assert settings.log_level == "DEBUG"


def test_list_parsing(monkeypatch):
    """Test that list environment variables are parsed correctly"""
    monkeypatch.setenv("ALLOWED_HOSTS", '["example.com", "api.example.com"]')

    settings = Settings()
    assert settings.allowed_hosts == ["example.com", "api.example.com"]


def test_boolean_parsing(monkeypatch):
    """Test that boolean environment variables are parsed correctly"""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ENABLE_CORS", "false")

    settings = Settings()
    assert settings.debug is True
    assert settings.enable_cors is False
