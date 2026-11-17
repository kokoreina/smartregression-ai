"""Versioned account contracts; secrets are excluded from repr and responses."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

Password = Annotated[SecretStr, Field(min_length=12, max_length=128)]
Token = Annotated[SecretStr, Field(min_length=40, max_length=256)]


class AuthValue(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmailInput(AuthValue):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalized(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class ProfileUpdate(AuthValue):
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("display_name", mode="before")
    @classmethod
    def clean_name(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise ValueError("invalid_display_name")
        return value


class Registration(EmailInput, ProfileUpdate):
    password: Password = Field(repr=False)


class Login(EmailInput):
    password: SecretStr = Field(min_length=1, max_length=128, repr=False)


class TokenInput(AuthValue):
    token: Token = Field(repr=False)


class PasswordReset(TokenInput):
    password: Password = Field(repr=False)


class PasswordChange(AuthValue):
    current_password: SecretStr = Field(min_length=1, max_length=128, repr=False)
    password: Password = Field(repr=False)


class CurrentUser(AuthValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    id: str
    email: EmailStr
    display_name: str
    verified: bool


class AuthMessage(AuthValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    message: str


class CsrfToken(AuthValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    token: str = Field(repr=False)


class AuthErrorResponse(AuthValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    code: str
    message: str


class WebCapabilities(AuthValue):
    schema_version: Literal["1.0.0"] = "1.0.0"
    local_demo: bool
