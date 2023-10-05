import time
import typing

from units_python.statement_build import Signature


def test():
    formal_time = int(time.time())
    actual_time = formal_time + 1
    type_time = actual_time + 1
    default_time = type_time + 1

    def formal(name: str):
        return f"_formal_{formal_time}_{name}"

    def actual(name: str):
        return f"_actual_{actual_time}_{name}"

    def type_(name: str):
        return f"_type_{type_time}_{name}"

    def default(name: str):
        return f"_default_{default_time}_{name}"

    def f1(_a: int, /, _b: str = "test", *, _c: float = .1, **_d: typing.Dict): pass

    sig = Signature(f1)
    assert sig.statement(formal, default) == \
           ((
                formal("_a"), "/",
                formal("_b") + "=" + default("_b"), "*",
                formal("_c") + "=" + default("_c"),
                "**" + formal("_d")
            ), {
                default("_b"): "test",
                default("_c"): .1,
            })
    assert sig.statement_with_type(formal, default, type_) == \
           ((
                f"{formal('_a')}: {type_('_a')}", "/",
                f"{formal('_b')}: {type_('_b')}={default('_b')}", "*",
                f"{formal('_c')}: {type_('_c')}={default('_c')}",
                f"**{formal('_d')}: {type_('_d')}"
            ), {
                type_("_a"): int,
                type_("_b"): str,
                type_("_c"): float,
                type_("_d"): typing.Dict,
            }, {
                default("_b"): "test",
                default("_c"): .1,
            })
    assert sig.call_statement(formal, actual) == \
           (actual("_a"),
            f"{formal('_b')}={actual('_b')}",
            f"{formal('_c')}={actual('_c')}",
            f"**{actual('_d')}")

    def f2(_a: dict = None, /, _b: list = any, *_c: tuple, **_d: map): pass

    sig = Signature(f2)
    assert sig.statement(formal, default) == \
           ((
                formal("_a") + "=" + default("_a"), "/",
                formal("_b") + "=" + default("_b"),
                f"*{formal('_c')}",
                f"**{formal('_d')}"
            ), {
                default("_a"): None,
                default("_b"): any,
            })
    assert sig.statement_with_type(formal, default, type_) == \
           ((
                f"{formal('_a')}: {type_('_a')}={default('_a')}", "/",
                f"{formal('_b')}: {type_('_b')}={default('_b')}",
                f"*{formal('_c')}: {type_('_c')}",
                f"**{formal('_d')}: {type_('_d')}",
            ), {
                type_("_a"): dict,
                type_("_b"): list,
                type_("_c"): tuple,
                type_("_d"): map,
            }, {
                default("_a"): None,
                default("_b"): any,
            })
    assert sig.call_statement(formal, actual) == \
           (f"{actual('_a')}",
            f"{formal('_b')}={actual('_b')}",
            f"*{actual('_c')}",
            f"**{actual('_d')}")
