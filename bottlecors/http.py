import enum


def parse_header_values(value):
    if not value:
        return []
    return [val.strip() for val in value.split(',')]


def make_header_value(values, transform=None):
    transform = transform if transform else lambda val: val
    return ', '.join(transform(val) for val in values)


def append_header(name, value, headers):
    values = headers.getlist(name)
    # if values:
    #     values = values.split(',')
    # else:
    #     values = []
    values.append(value)
    headers[name] = make_header_value(values)
    return headers


class StringEnum(str, enum.Enum):
    def __new__(cls, value):
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj


class HTTPMethod(StringEnum):
    CONNECT = 'CONNECT'
    DELETE = 'DELETE'
    GET = 'GET'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    POST = 'POST'
    PUT = 'PUT'
    TRACE = 'TRACE'


class HTTPHeader(StringEnum):
    ORIGIN = 'Origin'
    VARY = 'Vary'


class CORSHeader(StringEnum):
    REQUEST_METHOD = 'Access-Control-Request-Method'
    REQUEST_HEADERS = 'Access-Control-Request-Headers'
    ALLOW_ORIGIN = 'Access-Control-Allow-Origin'
    ALLOW_METHODS = 'Access-Control-Allow-Methods'
    ALLOW_HEADERS = 'Access-Control-Allow-Headers'
    EXPOSE_HEADERS = 'Access-Control-Expose-Headers'
    ALLOW_CREDENTIALS = 'Access-Control-Allow-Credentials'
    MAX_AGE = 'Access-Control-Max-Age'


class HeaderValue(StringEnum):
    TRUE = 'true'
    WILDCARD = '*'


HTTP_METHODS = frozenset((
    HTTPMethod.CONNECT, HTTPMethod.DELETE, HTTPMethod.GET, HTTPMethod.HEAD,
    HTTPMethod.OPTIONS, HTTPMethod.PATCH, HTTPMethod.POST, HTTPMethod.PUT,
    HTTPMethod.TRACE
))
