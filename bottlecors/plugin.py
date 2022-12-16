from http import HTTPStatus

import bottle

from bottlecors.http import HTTPMethod, HTTPHeader, CORSHeader, HeaderValue, \
    parse_header_values, make_header_value, append_header


class CORSPlugin:
    api = 2
    name = 'cors_plugin'

    def __init__(self, config):
        self._config = config

    def setup(self, app):
        routes = []
        for route in app.routes:
            if (
                route.method == 'PROXY' or
                route.method == HTTPMethod.OPTIONS
            ):
                continue
            option_route = bottle.Route(app, route.rule, HTTPMethod.OPTIONS,
                                        lambda *a, **ka: bottle.HTTPResponse(
                                            status=HTTPStatus.NO_CONTENT))
            routes.append(option_route)
        for route in routes:
            app.add_route(route)
        return None

    def apply(self, callback, route):

        def wrapper(*args, **kwargs):
            request_headers = bottle.request.headers
            need_raise = False
            if self._is_preflight_request(bottle.request):
                headers = self._get_preflight_response_headers(request_headers)
                response = bottle.HTTPResponse(status=HTTPStatus.NO_CONTENT)
            else:
                headers = self._get_actual_response_headers(request_headers)
                try:
                    response = callback(*args, **kwargs)
                except Exception as error:
                    need_raise = True
                    response = error
            # headers[HTTPHeader.VARY] = HTTPHeader.ORIGIN.value
                if not isinstance(response, bottle.HTTPResponse):
                    response = bottle.response
            append_header(HTTPHeader.VARY, HTTPHeader.ORIGIN, response.headers)
            if isinstance(response, bottle.HTTPResponse):
                response.headers.update(headers)
                return response
            bottle.response.headers.update(headers)
            if need_raise:
                raise
            return response

        return wrapper

    def _get_actual_response_headers(self, request_headers):
        headers = self._get_common_headers(request_headers)
        if not headers:
            return {}
        exposed_headers = self._get_response_header_value(
            self._config.exposed_headers,
            self._config.any_exposed_headers)
        if exposed_headers:
            exposed_headers = make_header_value(exposed_headers, str.title)
            headers[CORSHeader.EXPOSE_HEADERS] = exposed_headers
        return headers

    def _get_preflight_response_headers(self, request_headers):
        headers = self._get_common_headers(request_headers)
        if not headers:
            return {}
        requested_method = request_headers.get(CORSHeader.REQUEST_METHOD)
        if (
            not requested_method or
            not self._is_allowed_method(requested_method)
        ):
            return {}
        requested_headers = request_headers.get(CORSHeader.REQUEST_HEADERS)
        parsed_headers = parse_header_values(requested_headers)
        if not self._is_allowed_headers(parsed_headers):
            return {}
        allowed_methods = self._get_response_header_value(
            self._config.allowed_methods,
            self._config.any_methods,
            [requested_method])
        allowed_headers = self._get_response_header_value(
            self._config.allowed_headers,
            self._config.any_headers,
            parsed_headers)
        allowed_methods = make_header_value(allowed_methods, str.upper)
        headers[CORSHeader.ALLOW_METHODS] = allowed_methods
        allowed_headers = make_header_value(allowed_headers, str.title)
        if allowed_headers:
            headers[CORSHeader.ALLOW_HEADERS] = allowed_headers
        if self._config.max_age:
            headers[CORSHeader.MAX_AGE] = self._config.max_age
        return headers

    def _get_common_headers(self, request_headers):
        headers = {}
        origin = request_headers.get(HTTPHeader.ORIGIN)
        if not origin or not self._is_allowed_origin(origin):
            return headers
        if self._config.allowed_credentials:
            headers[CORSHeader.ALLOW_CREDENTIALS] = HeaderValue.TRUE.value
        if self._config.any_origins and not self._config.allowed_credentials:
            headers[CORSHeader.ALLOW_ORIGIN] = HeaderValue.WILDCARD.value
        else:
            headers[CORSHeader.ALLOW_ORIGIN] = origin
        return headers

    def _is_preflight_request(self, request):
        return (request.method == HTTPMethod.OPTIONS and
                CORSHeader.REQUEST_METHOD in request.headers)

    def _is_allowed_origin(self, origin):
        if self._config.any_origins or origin in self._config.allowed_origins:
            return True
        for pattern in self._config.allowed_origin_regexes:
            if pattern.fullmatch(origin):
                return True
        return False

    def _is_allowed_method(self, method):
        if self._config.any_methods or method in self._config.allowed_methods:
            return True
        return False

    def _is_allowed_headers(self, headers):
        if self._config.any_headers:
            return True
        return not (frozenset(hdr.lower() for hdr in headers) -
                    self._config.allowed_headers)

    def _get_response_header_value(self, values, allow_any,
                                   requested_values=None):
        if allow_any:
            if self._config.allowed_credentials:
                return requested_values or []
            return HeaderValue.WILDCARD
        return values
