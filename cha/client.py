import threading
import importlib
import sys
import os

from cha import config, utils, colors

# NOTE: this module is used  to lazy load the openai module and warm it up
_openai_module_instance = None


def _warm_openai_import_func():
    global _openai_module_instance
    try:
        _openai_module_instance = importlib.import_module("openai")
    except ImportError:
        # NOTE: if the import fails, _ensure_openai_module_is_loaded will handle it when a client is first requested.
        pass
    except Exception:
        # NOTE: Catch any other unexpected errors during background import, preventing the daemon thread from crashing
        # NOTE: this type of error will only surface if/when OpenAI client is requested
        pass


# start the warmup thread when this module is imported
warmup_thread_obj = threading.Thread(target=_warm_openai_import_func, daemon=True)
warmup_thread_obj.start()


def _ensure_openai_module_is_loaded():
    global _openai_module_instance
    if _openai_module_instance is None:
        # if warmup hasn't finished or failed, try importing directly
        try:
            import openai as openai_module_local

            _openai_module_instance = openai_module_local
        except ImportError as e:
            error_message = (
                f"Fatal Error: The 'openai' library is not installed or could not be imported. "
                f"Please install it: pip install openai. Details: {e}"
            )
            try:
                print(colors.red(error_message), file=sys.stderr)
            except Exception:
                print(error_message, file=sys.stderr)
            sys.exit(1)
    return _openai_module_instance


_default_openai_client_instance = None
_current_chat_client_instance = None


def get_default_openai_client():
    global _default_openai_client_instance
    if _default_openai_client_instance is None:
        openai_mod = _ensure_openai_module_is_loaded()
        utils.check_env_variable("OPENAI_API_KEY", config.OPENAI_DOCS_LINK)
        _default_openai_client_instance = openai_mod.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
    return _default_openai_client_instance


def get_current_chat_client():
    global _current_chat_client_instance
    if _current_chat_client_instance is None:
        _current_chat_client_instance = get_default_openai_client()
    return _current_chat_client_instance


def set_current_chat_client(api_key, base_url):
    global _current_chat_client_instance
    openai_mod = _ensure_openai_module_is_loaded()
    _current_chat_client_instance = openai_mod.OpenAI(
        api_key=api_key, base_url=base_url
    )
    return _current_chat_client_instance
