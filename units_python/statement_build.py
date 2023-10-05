import inspect
import typing

Parameter = inspect.Parameter
ParameterKind = Parameter.POSITIONAL_ONLY.__class__
T = typing.TypeVar("T")


class Signature:
    def __init__(self, fn: typing.Callable):
        self.__sigs = inspect.signature(fn)
        self.__pars = self.__sigs.parameters

    @property
    def return_annotation(self):
        if self.__sigs.return_annotation is self.__sigs.empty:
            return typing.Any
        return self.__sigs.return_annotation

    def call_statement(
            self,
            formal_name: typing.Callable[[str], str] = lambda name: name,
            actual_name: typing.Callable[[str], str] = lambda name: name
    ):
        """
        build call statement\n
        example: def demo(a, /, b, *, c, **d)
        return: ("a", "b=b", "c=c", "**d")
        :param formal_name: 自定义生成的形参命名
        :param actual_name: 自定义生成的实参命名
        :return: 参数调用数组
        """
        po, pok, vp, ko, vk = self.__arguments_assign_signature(self.__pars, formal_name, actual_name)
        return po + pok + vp + ko + vk

    def statement_with_type(self,
                            formal_name: typing.Callable[[str], str] = lambda name: name,
                            default_name: typing.Callable[[str], str] = lambda name: "_default_" + name,
                            type_name: typing.Callable[[str], str] = lambda name: "_type_" + name):
        """
        build function statement with type annotation
        :param formal_name:
        :param default_name:
        :param type_name:
        :return:
        """

        def build_name(name: str):
            return formal_name(name) + ": " + type_name(name)

        def build_type(name: str, _: Parameter):
            return type_name(name)

        def get_type_annotation(_: str, par: Parameter):
            if par.annotation is par.empty:
                return typing.Any
            return par.annotation

        po, pok, vp, ko, vk = self.__arguments_signature(self.__pars, build_name, default_name)
        po_n, pok_n, vp_n, ko_n, vk_n = self.traversal_parameters(self.__pars, build_type)
        po_t, pok_t, vp_t, ko_t, vk_t = self.traversal_parameters(self.__pars, get_type_annotation)
        type_dict = {}
        type_dict.update(zip(po_n, po_t))
        type_dict.update(zip(pok_n, pok_t))
        type_dict.update(zip(vp_n, vp_t))
        type_dict.update(zip(ko_n, ko_t))
        type_dict.update(zip(vk_n, vk_t))
        default_dict = self.__arguments_default(self.__pars, default_name)
        return (self.join_statement(po, pok, vp, ko, vk)), type_dict, default_dict

    def statement(self,
                  formal_name: typing.Callable[[str], str] = lambda name: name,
                  default_name: typing.Callable[[str], str] = lambda name: f"_default_{name}",
                  ):
        """
        build function statement\n
        example: def demo(a, /, b, *, c, **d): pass\n
        return: ("a", "/", "b", "*", "c", "**d")
        :param formal_name: 自定义生成的形参命名
        :param default_name: 自定义生成的默认参数命名
        :return: 函数形参数组
        """
        po, pok, vp, ko, vk = self.__arguments_signature(self.__pars, formal_name, default_name)
        default_dict = self.__arguments_default(self.__pars, default_name)
        return self.join_statement(po, pok, vp, ko, vk), default_dict

    @staticmethod
    def join_statement(position_only: typing.Sequence[str],
                       position_or_key: typing.Sequence[str],
                       var_position: typing.Sequence[str],
                       key_only: typing.Sequence[str],
                       var_key: typing.Sequence[str]):
        args = []
        args.extend(position_only)
        if len(position_only) != 0:
            args.append("/")
        args.extend(position_or_key)
        args.extend(var_position)
        if len(key_only) != 0:
            args.append("*")
        args.extend(key_only)
        args.extend(var_key)
        return tuple(args)

    @classmethod
    def __arguments_default(cls, parameters: typing.Mapping[str, Parameter], default_name: typing.Callable[[str], str]):
        def default_rename(n: str, par: Parameter):
            return default_name(n), par.default

        default_dict = {}
        for item in cls.traversal_parameters(parameters, default_rename):
            for name, default_value in item:
                if default_value is Parameter.empty:
                    continue
                default_dict[name] = default_value

        return default_dict

    @classmethod
    def __arguments_assign_signature(cls, parameters: typing.Mapping[str, Parameter],
                                     formal_name: typing.Callable[[str], str],
                                     actual_name: typing.Callable[[str], str]):
        def argument_assign_signature(name: str, par: Parameter):
            return cls.__argument_assign_signature(formal_name(name), actual_name(name), par.kind)

        return cls.traversal_parameters(parameters, argument_assign_signature)

    @classmethod
    def __arguments_signature(cls, parameters: typing.Mapping[str, Parameter],
                              formal_name: typing.Callable[[str], str],
                              default_name: typing.Callable[[str], str]):
        def argument_signature(name: str, par: Parameter):
            if par.default is par.empty:
                return cls.__argument_signature(formal_name(name), par.kind)
            return cls.__argument_signature(formal_name(name), par.kind) + "=" + default_name(name)

        return cls.traversal_parameters(parameters, argument_signature)

    @staticmethod
    def traversal_parameters(parameters: typing.Mapping[str, Parameter],
                             fn: typing.Callable[[str, Parameter], T]):
        positional_only = []
        positional_or_keyword = []
        var_positional = []
        keyword_only = []
        var_keyword = []

        for name, par in parameters.items():
            if par.kind is par.POSITIONAL_ONLY:
                positional_only.append(fn(name, par))
            elif par.kind is par.POSITIONAL_OR_KEYWORD:
                positional_or_keyword.append(fn(name, par))
            elif par.kind is par.VAR_POSITIONAL:
                var_positional.append(fn(name, par))
            elif par.kind is par.KEYWORD_ONLY:
                keyword_only.append(fn(name, par))
            elif par.kind is par.VAR_KEYWORD:
                var_keyword.append(fn(name, par))
            else:
                raise TypeError(f"unknown parameter kind: {par}")

        return tuple(positional_only), \
            tuple(positional_or_keyword), \
            tuple(var_positional), \
            tuple(keyword_only), \
            tuple(var_keyword)

    @staticmethod
    def __argument_assign_signature(formal_arg: str, actual_arg: str, kind: ParameterKind):
        if kind is ParameterKind.POSITIONAL_ONLY:
            return actual_arg
        elif kind is ParameterKind.POSITIONAL_OR_KEYWORD:
            return formal_arg + "=" + actual_arg
        elif kind is ParameterKind.VAR_POSITIONAL:
            return "*" + actual_arg
        elif kind is ParameterKind.KEYWORD_ONLY:
            return formal_arg + "=" + actual_arg
        elif kind is ParameterKind.VAR_KEYWORD:
            return "**" + actual_arg
        else:
            raise TypeError(f"unknown parameter kind: {kind}")

    @staticmethod
    def __argument_signature(name: str, kind: ParameterKind):
        if kind is kind.POSITIONAL_ONLY:
            return name
        elif kind is kind.POSITIONAL_OR_KEYWORD:
            return name
        elif kind is kind.VAR_POSITIONAL:
            return "*" + name
        elif kind is kind.KEYWORD_ONLY:
            return name
        elif kind is kind.VAR_KEYWORD:
            return "**" + name
        else:
            raise TypeError(f"unknown parameter kind: {kind}")


__all__ = [
    "Signature",
]
