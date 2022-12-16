import re
from contextlib import nullcontext

import pytest

from bottlecors import CORSConfig
from bottlecors.http import HTTPMethod, HTTP_METHODS, HeaderValue


def test_default_init_config():
    config = CORSConfig()
    assert config.max_age == 0
    assert config.allowed_origin_regexes == ()
    assert config.allowed_credentials is False
    assert config.any_origins is True
    assert config.any_methods is False
    assert config.any_headers is False
    assert config.any_exposed_headers is False
    assert config.allowed_origins == frozenset([HeaderValue.WILDCARD])
    assert config.allowed_headers == frozenset(['Content-Type'])
    assert config.allowed_methods == frozenset([HTTPMethod.DELETE,
                                                HTTPMethod.GET,
                                                HTTPMethod.PATCH,
                                                HTTPMethod.POST,
                                                HTTPMethod.PUT])


@pytest.mark.parametrize(
    'allowed_origins,allowed_methods,allowed_headers,exposed_headers,'
    'allowed_origin_regexes,allowed_credentials,max_age',
    [
        ((), (), (), (), (), False, 0),
        ([HeaderValue.WILDCARD], [HeaderValue.WILDCARD],
         [HeaderValue.WILDCARD], [HeaderValue.WILDCARD], ['.*'], True, 1),
        (
            ['http://foo.bar'], ['GET'], ['Host'], ['Content-Type'],
            [r'http://.*\.bar'], True, 86400
        ),
        (
            ('https://foo.bar/path/', 'http://foo:8080'), tuple(HTTP_METHODS),
            ('Origin', 'Vary'), ('Content-Disposition', 'Keep-Alive'),
            (r'https?://[fo]{3}\.b|rar', r'https://.*:?\d{2-4}'), False, 0
        )
    ]
)
def test_init_config(allowed_origins, allowed_methods, allowed_headers,
                     allowed_origin_regexes, exposed_headers,
                     allowed_credentials, max_age):
    with nullcontext():
        config = CORSConfig(allowed_origins, allowed_methods, allowed_headers,
                            allowed_credentials, allowed_origin_regexes,
                            exposed_headers, max_age)
        assert config.max_age == max_age
        assert config.allowed_credentials is allowed_credentials
        assert config.allowed_origins == frozenset(allowed_origins)
        assert config.allowed_methods == frozenset(allowed_methods)
        assert config.allowed_headers == frozenset(allowed_headers)
        assert config.exposed_headers == frozenset(exposed_headers)
        assert config.any_origins is (HeaderValue.WILDCARD in allowed_origins)
        assert config.any_methods is (HeaderValue.WILDCARD in allowed_methods)
        assert config.any_headers is (HeaderValue.WILDCARD in allowed_headers)
        assert config.any_exposed_headers is (HeaderValue.WILDCARD in
                                              exposed_headers)
        assert (
            config.allowed_origin_regexes ==
            tuple(map(re.compile, allowed_origin_regexes))
        )


@pytest.mark.parametrize(
    'invalid_args,exception',
    [
        ({'allowed_origins': ''}, TypeError),
        ({'allowed_origins': ['https://foo', 1]}, TypeError),
        ({'allowed_origins': ['']}, ValueError),
        ({'allowed_origins': ['foo.bar']}, ValueError),
        ({'allowed_origins': ['https://foo', 'http://']}, ValueError),

        ({'allowed_methods': 'OPTIONS'}, TypeError),
        ({'allowed_methods': ['PUT', 1]}, TypeError),
        ({'allowed_methods': ['']}, ValueError),
        ({'allowed_methods': ['get']}, ValueError),
        ({'allowed_methods': ['GET', 'post']}, ValueError),
        ({'allowed_methods': ['Get', 'POST']}, ValueError),

        ({'allowed_headers': 'Host'}, TypeError),
        ({'allowed_headers': ['Origin', 1]}, TypeError),
        ({'allowed_headers': ['']}, ValueError),

        ({'exposed_headers': 'Content-Type'}, TypeError),
        ({'allowed_headers': ['Origin', 1]}, TypeError),
        ({'allowed_headers': ['']}, ValueError),

        ({'allowed_origin_regexes': '.*'}, TypeError),
        ({'allowed_origin_regexes': ['.*(']}, ValueError),

        ({'allowed_credentials': 0}, TypeError),
        ({'allowed_credentials': 1}, TypeError),

        ({'max_age': ''}, TypeError),
        ({'max_age': True}, TypeError),
        ({'max_age': -1}, ValueError),
    ]
)
def test_fail_init_config(invalid_args, exception):
    with pytest.raises(exception):
        assert CORSConfig(**invalid_args)
