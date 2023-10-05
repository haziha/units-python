import abc
import inspect
import time
import traceback
import types
import typing
import warnings

from .statement_build import Signature
from .units import T


class _Checkpoint(typing.Protocol):
    def enter(self, args: typing.Tuple[typing.Any], kwargs: typing.Dict[str, typing.Any]):
        pass

    def exit(self, result: typing.Union[None, typing.Tuple[typing.Any]]):
        pass

    def exception(self, exc: Exception):
        pass


class Checkpoint(abc.ABC):
    @abc.abstractmethod
    def enter(self, args: typing.Tuple[typing.Any], kwargs: typing.Dict[str, typing.Any]):
        pass

    @abc.abstractmethod
    def exit(self, result: typing.Union[None, typing.Tuple[typing.Any]]):
        pass

    @abc.abstractmethod
    def exception(self, exc: Exception):
        pass


_CheckpointT = typing.Callable[[types.FunctionType], _Checkpoint]


class Hook:
    def __init__(self):
        self.__checkpoints: typing.List[_CheckpointT] = []

    def add_checkpoint(self, checkpoint: _CheckpointT):
        self.__checkpoints.append(checkpoint)

    def __init_call(self, fn: types.FunctionType):
        checkpoints = []
        for checkpoint in self.__checkpoints:
            try:
                if cp := checkpoint(fn):
                    checkpoints.append(cp)
            except Exception as e:
                warnings.warn(f"initial checkpoint error: {checkpoint}")
                traceback.print_exception(type(e), e, e.__traceback__)
        return tuple(checkpoints)

    @staticmethod
    def __before_call(checkpoints: typing.Iterable[_Checkpoint],
                      args: typing.Tuple[typing.Any],
                      kwargs: typing.Dict[str, typing.Any]):
        for checkpoint in checkpoints:
            try:
                checkpoint.enter(args, kwargs.copy())
            except Exception as e:
                warnings.warn(f"enter checkpoint error: {checkpoint}")
                traceback.print_exception(type(e), e, e.__traceback__)

    @staticmethod
    def __after_call(checkpoints: typing.Tuple[_Checkpoint], result: typing.Union[None, typing.Tuple[typing.Any]]):
        for checkpoint in checkpoints:
            try:
                checkpoint.exit(result)
            except Exception as e:
                warnings.warn(f"exit checkpoint error: {checkpoint}")
                traceback.print_exception(type(e), e, e.__traceback__)

    @staticmethod
    def __exception_call(checkpoints: typing.Tuple[_Checkpoint], exc: Exception):
        for checkpoint in checkpoints:
            try:
                checkpoint.exception(exc)
            except Exception as e:
                warnings.warn(f"exception checkpoint error: {checkpoint}")
                traceback.print_exception(type(e), e, e.__traceback__)

    def hook(self, cls: T) -> T:
        for c in inspect.getmro(cls):
            self.__hook(c)
        return cls

    def __hook(self, cls: typing.Type):
        for name, item in cls.__dict__.items():  # type: str, typing.Any
            if isinstance(item, types.FunctionType):
                fn = item
            elif isinstance(item, classmethod):
                fn = item.__func__
            elif isinstance(item, staticmethod):
                fn = item.__func__
            else:
                continue
            fn = self.__hook_function(name, fn)
            if isinstance(item, types.FunctionType):
                setattr(cls, name, fn)
            elif isinstance(item, classmethod):
                setattr(cls, name, classmethod(fn))
            elif isinstance(item, staticmethod):
                setattr(cls, name, staticmethod(fn))

    def __hook_function(self, name: str, fn: types.FunctionType):
        random_prefix = str(int(time.time()))
        sig = Signature(fn)
        args, args_type, args_default = sig.statement_with_type()
        args_call = sig.call_statement()
        ln = {}
        exec(f"def {name}({', '.join(args)}):\n"
             f"    _{random_prefix}_bind = _{random_prefix}_signature.bind({', '.join(args_call)})\n"
             f"    _{random_prefix}_bind.apply_defaults()\n"
             f"    _{random_prefix}_checkpoints = _{random_prefix}_init(_{random_prefix}_{name})\n"
             f"    _{random_prefix}_before(_{random_prefix}_checkpoints,"
             f"_{random_prefix}_bind.args, _{random_prefix}_bind.kwargs)\n"
             f"    try:\n"
             f"        _{random_prefix}_result = _{random_prefix}_{name}({', '.join(args_call)})\n"
             f"    except Exception as _{random_prefix}_exception:\n"
             f"        _{random_prefix}_exception(_{random_prefix}_exception)\n"
             f"    else:\n"
             f"        _{random_prefix}_after(_{random_prefix}_checkpoints, _{random_prefix}_result)",
             {
                 f"_{random_prefix}_{name}": fn,
                 f"_{random_prefix}_signature": sig.signature,
                 f"_{random_prefix}_init": self.__init_call,
                 f"_{random_prefix}_before": self.__before_call,
                 f"_{random_prefix}_after": self.__after_call,
                 f"_{random_prefix}_exception": self.__exception_call,
                 **args_type,
                 **args_default,
             }, ln)
        return ln[name]


__all__ = [
    "Hook",
    "Checkpoint",
]
