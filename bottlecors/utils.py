from collections.abc import Sequence


def is_container(value):
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))
