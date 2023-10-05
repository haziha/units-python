import types

from units_python.function_hook import Hook, Checkpoint

hook = Hook()


@hook.hook
class Demo:
    def __init__(self):
        print(self)

    def a(self, a: int, b: float, /, c, d=1, *, e=1):
        print(self, a, b, c, d, e)

    @classmethod
    def b(cls, a: int, b: float, /, c, d=1, *, e=1):
        print(cls, a, b, c, d, e)

    @staticmethod
    def c(a: int, b: float, /, c, d=1, *, e=1):
        print(a, b, c, d, e)


class Cp(Checkpoint):
    def __init__(self, fn: types.FunctionType):
        print(fn)

    def enter(self, args, kwargs):
        print(args, kwargs)

    def exit(self, result):
        print(result)

    def exception(self, exc: Exception):
        print(exc)


hook.add_checkpoint(lambda fn: Cp(fn))


def test():
    d = Demo()
    d.a(0, 1., 2, d=3, e=4)
    d.b(0, 1., 2, d=3, e=4)
    d.c(0, 1., 2, d=3, e=4)
