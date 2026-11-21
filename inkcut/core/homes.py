# -*- coding: utf-8 -*-
"""
Copyright (c) 2026, The Inkcut Team

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import os


# The only reader of the XDG home variables.
_APP = 'inkcut'
_STATE_RECORD = 'state-home'


def _set_path(name):
    # Blank is unset. An empty value must not become a relative path.
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return os.path.expanduser(value)


def _live(app_var, xdg_var, default_parts):
    app_path = _set_path(app_var)
    if app_path is not None:
        return app_path
    xdg_path = _set_path(xdg_var)
    if xdg_path is not None:
        return os.path.join(xdg_path, _APP)
    return os.path.join(os.path.expanduser('~'), *(default_parts + (_APP,)))


def config_home():
    return _live('INKCUT_CONFIG_HOME', 'XDG_CONFIG_HOME', ('.config',))


def data_home():
    return _live('INKCUT_DATA_HOME', 'XDG_DATA_HOME', ('.local', 'share'))


def cache_home():
    return _live('INKCUT_CACHE_HOME', 'XDG_CACHE_HOME', ('.cache',))


def runtime_dir():
    app_path = _set_path('INKCUT_RUNTIME_DIR')
    if app_path is not None:
        return app_path
    xdg_path = _set_path('XDG_RUNTIME_DIR')
    if xdg_path is not None:
        return os.path.join(xdg_path, _APP)
    raise RuntimeError('INKCUT_RUNTIME_DIR or XDG_RUNTIME_DIR is required')


def _state_record_path():
    # No install command records homes. The pin is a file in the config
    # home, which the app already uses. It is not a new data directory.
    return os.path.join(config_home(), _STATE_RECORD)


def _read_state_record():
    try:
        with open(_state_record_path(), 'r') as record:
            path = record.read().strip()
    except OSError:
        return None
    if not path:
        return None
    return path


def _write_state_record(path):
    record_path = _state_record_path()
    directory = os.path.dirname(record_path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    temporary = record_path + '.tmp'
    with open(temporary, 'w') as record:
        record.write(path + '\n')
    os.replace(temporary, record_path)


def state_home():
    # Pinned on first resolve. A later state variable does not move it.
    recorded = _read_state_record()
    if recorded is not None:
        return recorded
    path = os.path.abspath(_live(
        'INKCUT_STATE_HOME', 'XDG_STATE_HOME', ('.local', 'state')))
    _write_state_record(path)
    return path


def log_dir():
    return os.path.join(state_home(), 'logs')
