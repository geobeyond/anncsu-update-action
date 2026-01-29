"""
Configuration settings for anncsu-update-action.

This module provides settings classes that load configuration from environment
variables or .env files using pydantic-settings.

"""

from __future__ import annotations
from typing_extensions import Annotated

from pydantic import Field, model_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnncsuUpdateSettings(BaseSettings):
    """Settings for loading client assertion configuration from environment variables.

    This class uses pydantic-settings to load configuration from environment
    variables or a .env file. All environment variables are prefixed with `ANNCSU_UPDATE_`.

    IMPORTANT: ALL ANNCSU_UPDATE_* variables must be present in .env (can be empty).
    The validation happens at initialization time.

    Environment Variables:
        ANNCSU_UPDATE_CODICE_COMUNE: Comune ISTAT id.

    Example .env file:
        ANNCSU_UPDATE_CODICE_COMUNE=I501

    """

    model_config = SettingsConfigDict(
        env_prefix="ANNCSU_UPDATE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    codice_comune: Annotated[
        str,
        Field(description="Codice Comune as ISTAT code"),
    ]

    @model_validator(mode="after")
    def validate_all_keys_present(self) -> "AnncsuUpdateSettings":
        """Validate that ALL ANNCSU_UPDATE_* variables are present in .env or environment.

        The variables can have empty values (""), but they must be defined (not None).
        None means the variable was never set, "" means it was set but empty.

        Raises:
            ValidationError: If any required variable is not defined
        """
        value = getattr(self, "codice_comune", None)
        # None means not defined at all, "" is valid (defined but empty)
        if value is None:
            raise ValidationError(
                "Missing required environment variables in .env:\n"
                + "\nANNCSU_UPDATE_CODICE_COMUNE"
                + "\n\nAll nANNCSU_UPDATE_CODICE_COMUNE* variables must be present (can be empty)."
            )

        return self


__all__ = [
    "AnncsuUpdateSettings",
]
