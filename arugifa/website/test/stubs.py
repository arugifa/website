"""Test helpers to write stubs."""

import inspect
from inspect import getmembers, isbuiltin, isclass, isfunction, signature

POSITIONAL_OR_KEYWORD = inspect._ParameterKind.POSITIONAL_OR_KEYWORD
POSITIONAL_ONLY = inspect._ParameterKind.POSITIONAL_ONLY


def stub(original, classified=False):  # noqa: C901
    """Check that the signature of a stub is up-to-date with the ``original`` object.

    To be used as follows::

        @stub(object_to_stub)
        def stub_implementation():
            ...

    The main purpose is to avoid bugs to sneak in the codebase. This can happen:

    - if keyword arguments are used in interface tests when checking stub behaviors,
    - but positional arguments are used everywhere else in the codebase.

    In this case, if the signature of function/methods tested changes (e.g., when
    upgrading their library), then the interface tests would remain GREEN, but the
    codebase would miserably crashes when shipped into production.

    :param classified:
        set to ``True`` when using an instance method to make a function stub.
        This will remove the ``self`` attribute from the stub signature,
        so both the stub method and the original function have the same signature.
        Using methods is useful to generate side effects on the fly, depending on
        the stub instance attributes.
    """
    def wrapper(obj):
        try:
            if isfunction(obj):
                original_fqin = fqin(original)
                stub_fqin = fqin(obj)

                original_signature = signature(original)
                stub_signature = signature(obj)

                if classified:
                    parameters = filter(
                        lambda p: p.name != 'self',
                        stub_signature.parameters.values(),
                    )
                    stub_signature = stub_signature.replace(
                        parameters=parameters)

                if isbuiltin(original):
                    def update_param(p):
                        if p.kind == POSITIONAL_ONLY:
                            return p.replace(kind=POSITIONAL_OR_KEYWORD)
                        return p

                    parameters = map(
                        update_param,
                        original_signature.parameters.values(),
                    )
                    original_signature = original_signature.replace(
                        parameters=parameters)

                assert stub_signature == original_signature

            elif isclass(obj):
                def is_method(attr):
                    return isfunction(attr) and attr.__name__ in original.__dict__  # noqa: E501

                methods = getmembers(obj, is_method)

                for name, stub_method in methods:
                    original_method = getattr(original, name)

                    original_fqin = fqin(original_method)
                    stub_fqin = fqin(stub_method)

                    original_signature = signature(original_method)
                    stub_signature = signature(stub_method)

                    assert stub_signature == original_signature

            else:
                error = f"{stub_fqin} should be either a class or a function"
                raise TypeError(error)

        except AssertionError:
            error = (
                f'Signature of {stub_fqin} differs from {original_fqin}: '
                f'{stub_signature} != {original_signature}'
            )
            raise ValueError(error)

        return obj

    return wrapper


def fqin(obj):
    """Return the Fully Qualified Import Name of an object."""
    return f'{obj.__module__}.{obj.__qualname__}'
