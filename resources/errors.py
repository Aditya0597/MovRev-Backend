class InternalServerError(Exception):
    pass


class SchemaValidationException(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class MovieNotExistsError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
    pass


class EmailNotExistsError(Exception):
    pass


class BadTokenError(Exception):
    pass


class UnauthorizedError(Exception):
    pass
