from functools import wraps


class MetaFactory(type):
    _registry = {}

    def __new__(cls, name, bases, class_dict):
        class_dict["_registry"] = {}
        klass = super().__new__(cls, name, bases, class_dict)
        return klass

    def __init__(cls, name, bases, class_dict):
        super().__init__(name, bases, class_dict)

        if not cls.__abstractmethods__:
            for base in bases:
                if isinstance(base, MetaFactory):
                    base._registry[name] = cls


def create_factory(name):
    """Factory factory"""  # factory for factories because why not

    @wraps(name)
    class KlassFactory:
        @staticmethod
        def _retrieve_from_registry(abc_type, subclass_type):
            if abc_type not in name._registry:
                raise ValueError(f"No such factory-enabled ABC: {abc_type}")
            abc_cls = name._registry[abc_type]

            if subclass_type not in abc_cls._registry:
                raise ValueError(
                    f"No subclass {subclass_type} registered for {abc_type}"
                )
            return abc_cls._registry[subclass_type]

        @staticmethod
        def create(abc_type, subclass_type, **kwargs):
            klass = KlassFactory._retrieve_from_registry(abc_type, subclass_type)
            return klass(**kwargs)

        @staticmethod
        def from_dict(abc_type, subclass_type, data):
            klass = KlassFactory._retrieve_from_registry(abc_type, subclass_type)
            return klass.from_dict(data)

    # Dynamically set the class name:
    KlassFactory.__name__ = f"{name.__name__}Factory"
    return KlassFactory
