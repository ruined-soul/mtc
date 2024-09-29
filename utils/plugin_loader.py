import importlib
import os

PLUGIN_FOLDER = 'plugins/'

def load_plugin(plugin_name):
    try:
        module = importlib.import_module(f'{PLUGIN_FOLDER}.{plugin_name}')
        if hasattr(module, 'register_handlers'):
            module.register_handlers(dispatcher)
        return True
    except Exception as e:
        return False

def unload_plugin(plugin_name):
    try:
        module = importlib.import_module(f'{PLUGIN_FOLDER}.{plugin_name}')
        if hasattr(module, 'unregister_handlers'):
            module.unregister_handlers(dispatcher)
        del sys.modules[f'{PLUGIN_FOLDER}.{plugin_name}']
        return True
    except Exception as e:
        return False
