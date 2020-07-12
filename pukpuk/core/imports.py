import importlib


DEFAULT_MODULE_CLASS = 'Module'


def class_import(path):
    path_module = importlib.import_module(path)
    clss = getattr(path_module, DEFAULT_MODULE_CLASS)
    return clss
