from http import HTTPStatus

import bottle

from bottlecors.http import HTTPMethod, HTTPHeader, CORSHeader, HeaderValue, \
    parse_header_values, make_header_value, append_header


# class HandleErrorPlugin:
#     api = 2
#     name = 'error_handling_plugin'
#
#     def apply(self, callback, route):
#         def wrapper(*args, **kwargs):
#             return callback(*args, **kwargs)
#             try:
#                 response = callback(*args, **kwargs)
#             except Exception as error:
#                 if not isinstance(error, bottle.HTTPError):
#                     response = bottle.HTTPError(500, {'a': 1}, exception=error)
#             return response
#         return wrapper


class CORSPlugin:
    api = 2
    name = 'cors_plugin'

    _EXCLUDED_METHODS = frozenset(('PROXY', HTTPMethod.OPTIONS))

    def __init__(self, config):
        self._config = config

    def setup(self, app):
        routes = []
        self._register_error_handlers(app)
        for route in app.routes:
            if route.method in self._EXCLUDED_METHODS:
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
            if self._is_preflight_request(bottle.request):
                return self._handle_preflight_request(bottle.request.headers)
            return self._handle_actual_request(bottle.request.headers,
                                               callback, args, kwargs)
        return wrapper

    def _wrap_error_handler(self, handler):
        def handle_error(response):
            if CORSHeader.ALLOW_ORIGIN not in response:
                headers = self._get_actual_response_headers(bottle.
                                                            request.headers)
                response.headers.update(headers)
            return handler(response)
        return handle_error

    def _register_error_handlers(self, app):
        for status in self._config.wrap_error_statuses:
            app.error_handler[status] = self._wrap_error_handler(
                app.error_handler.get(status, app.default_error_handler)
            )

    def _handle_preflight_request(self, request_headers):
        headers = self._get_preflight_response_headers(request_headers)
        return bottle.HTTPResponse(status=HTTPStatus.NO_CONTENT,
                                   headers=headers)

    def _handle_actual_request(self, request_headers, callback, args, kwargs):
        body = None
        error = None
        headers = self._get_actual_response_headers(request_headers)
        try:
            response = callback(*args, **kwargs)
        except bottle.HTTPError as http_error:
            error = http_error
            response = http_error
        else:
            if not isinstance(response, bottle.HTTPResponse):
                body = response
                response = bottle.response
        response.headers.update(headers)
        if error:
            raise error
        return body or response

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
        headers = {HTTPHeader.VARY: HTTPHeader.ORIGIN.value}
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
