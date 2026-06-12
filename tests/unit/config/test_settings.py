from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from packages.config.settings import SuperlinkedSettings


def test_superlinked_settings_normalize_base_url() -> None:
    settings = SuperlinkedSettings(
        sie_base_url="https://example.com/",
        sie_api_key=SecretStr("test-key"),
    )

    assert settings.sie_base_url == "https://example.com"
    assert settings.api_key_value == "test-key"


def test_superlinked_settings_reject_invalid_base_url() -> None:
    with pytest.raises(ValidationError):
        SuperlinkedSettings(sie_base_url="not-a-url")
