import inspect
import typing

Parameter = inspect.Parameter
ParameterKind = Parameter.POSITIONAL_ONLY.__class__
T = typing.TypeVar("T")

__all__ = [
    "Parameter",
    "ParameterKind",
    "T",
]
