import re
import urllib.parse
from http import HTTPStatus

from bottlecors.http import HTTP_METHODS, HTTPMethod, HeaderValue
from bottlecors.utils import is_container


class CORSConfig:

    _DEFAULT_ALLOWED_ORIGINS = (HeaderValue.WILDCARD,)
    _DEFAULT_ALLOWED_METHODS = (HTTPMethod.DELETE, HTTPMethod.GET,
                                HTTPMethod.PATCH, HTTPMethod.POST,
                                HTTPMethod.PUT)
    _DEFAULT_ALLOWED_HEADERS = ('Content-Type',)
    _DEFAULT_ALLOWED_CREDENTIALS = False
    _DEFAULT_ALLOWED_ORIGIN_REGEXES = ()
    _DEFAULT_EXPOSED_HEADERS = ()
    _DEFAULT_MAX_AGE = 0
    _DEFAULT_WRAP_ERROR_STATUSES = (HTTPStatus.BAD_REQUEST,
                                    HTTPStatus.UNAUTHORIZED,
                                    HTTPStatus.FORBIDDEN,
                                    HTTPStatus.NOT_FOUND,
                                    HTTPStatus.METHOD_NOT_ALLOWED,
                                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                                    HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
                                    HTTPStatus.INTERNAL_SERVER_ERROR)

    __slots__ = ('allowed_origins', 'allowed_methods', 'allowed_headers',
                 'allowed_credentials', 'allowed_origin_regexes',
                 'exposed_headers', 'max_age', 'any_origins', 'any_methods',
                 'any_headers', 'any_exposed_headers', 'wrap_error_statuses')

    def __init__(self,
                 allowed_origins=_DEFAULT_ALLOWED_ORIGINS,
                 allowed_methods=_DEFAULT_ALLOWED_METHODS,
                 allowed_headers=_DEFAULT_ALLOWED_HEADERS,
                 allowed_credentials=_DEFAULT_ALLOWED_CREDENTIALS,
                 allowed_origin_regexes=_DEFAULT_ALLOWED_ORIGIN_REGEXES,
                 exposed_headers=_DEFAULT_EXPOSED_HEADERS,
                 max_age=_DEFAULT_MAX_AGE,
                 wrap_error_statuses=_DEFAULT_WRAP_ERROR_STATUSES):
        self.allowed_origins = self._parse_origins(allowed_origins)
        self.allowed_methods = self._parse_methods(allowed_methods)
        self.allowed_headers = self._parse_headers(allowed_headers)
        self.exposed_headers = self._parse_headers(exposed_headers)
        self.allowed_origin_regexes = self._parse_regexes(
            allowed_origin_regexes)
        self._validate_max_age(max_age)
        if not isinstance(allowed_credentials, bool):
            raise TypeError('allowed_credential must be bool type')
        self.max_age = max_age
        self.allowed_credentials = allowed_credentials
        self.any_origins = self._has_wildcard(self.allowed_origins)
        self.any_methods = self._has_wildcard(self.allowed_methods)
        self.any_headers = self._has_wildcard(self.allowed_headers)
        self.any_exposed_headers = self._has_wildcard(self.exposed_headers)
        self.wrap_error_statuses = wrap_error_statuses

    def _has_wildcard(self, values):
        return HeaderValue.WILDCARD in values

    def _parse_wildcarded_values(self, values, validate=None):
        if not is_container(values):
            raise TypeError(f'expected iterable got {type(values)}')
        validate = validate if validate else lambda v: v
        for value in values:
            if not isinstance(value, str):
                raise TypeError(f'expected str type got {type(value)}')
            if not value:
                raise ValueError('value can\'t be empty')
            if value == HeaderValue.WILDCARD:
                return frozenset([HeaderValue.WILDCARD])
            validate(value)
        return frozenset(values)

    def _parse_origins(self, origins):
        return self._parse_wildcarded_values(origins, self._validate_origin)

    def _parse_methods(self, methods):
        return self._parse_wildcarded_values(methods, self._validate_method)

    def _parse_headers(self, headers):
        return self._parse_wildcarded_values(headers)

    def _parse_regexes(self, regexes):
        if not is_container(regexes):
            raise TypeError(f'expected iterable got {type(regexes)}')
        try:
            return tuple(map(re.compile, regexes))
        except re.error as error:
            raise ValueError(f'Invalid regexp: {error}')

    def _validate_origin(self, origin):
        parsed = urllib.parse.urlparse(origin)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f'Invalid origin value: {origin}')
        return None

    def _validate_method(self, method):
        if method not in HTTP_METHODS:
            raise ValueError(f'Invalid HTTP method: {method}')
        return None

    def _validate_max_age(self, max_age):
        if not isinstance(max_age, int) or isinstance(max_age, bool):
            raise TypeError('max_age must be int type')
        if max_age < 0:
            raise ValueError('max_age value must be positive')
        return max_age
