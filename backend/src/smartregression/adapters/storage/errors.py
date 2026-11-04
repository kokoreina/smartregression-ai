"""Safe storage configuration failures; never include supplied values."""


class DatabaseConfigurationError(ValueError):
    code = "database_configuration_invalid"

    def __init__(self) -> None:
        super().__init__(self.code)
