"""
Copyright (c) 2026, The Inkcut Team

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import logging
import os
from pathlib import Path

import pytest
from enaml.workbench.api import PluginManifest

from inkcut.core.homes import (
    cache_home, config_home, data_home, log_dir, runtime_dir, state_home,
)
from inkcut.core.models import Plugin


_HOME_VARS = (
    'HOME',
    'INKCUT_CONFIG_HOME',
    'INKCUT_DATA_HOME',
    'INKCUT_STATE_HOME',
    'INKCUT_CACHE_HOME',
    'INKCUT_RUNTIME_DIR',
    'XDG_CONFIG_HOME',
    'XDG_DATA_HOME',
    'XDG_STATE_HOME',
    'XDG_CACHE_HOME',
    'XDG_RUNTIME_DIR',
)

_XDG_HOME_VARS = (
    'XDG_CONFIG_HOME',
    'XDG_DATA_HOME',
    'XDG_STATE_HOME',
    'XDG_CACHE_HOME',
    'XDG_RUNTIME_DIR',
)


@pytest.fixture(autouse=True)
def temp_home(monkeypatch, tmp_path):
    """Point homes at a temporary directory, never the real home."""
    home = tmp_path / 'home'
    home.mkdir()
    for name in _HOME_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    return home


def _plugin(plugin_id):
    return Plugin(manifest=PluginManifest(id=plugin_id))


def test_config_home_uses_a_set_app_variable(temp_home, monkeypatch):
    chosen = temp_home / 'custom' / 'inkcut'
    monkeypatch.setenv('INKCUT_CONFIG_HOME', str(chosen))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(temp_home / 'xdg'))
    assert config_home() == str(chosen)
    assert _plugin('inkcut.device')._state_file == str(
        chosen / 'inkcut.device.json')


def test_config_home_uses_xdg_when_the_app_variable_is_unset(
        temp_home, monkeypatch):
    xdg = temp_home / 'xdg'
    monkeypatch.setenv('XDG_CONFIG_HOME', str(xdg))
    assert config_home() == str(xdg / 'inkcut')
    assert _plugin('inkcut.device')._state_file == str(
        xdg / 'inkcut' / 'inkcut.device.json')


def test_config_home_defaults_to_the_spec_path(temp_home):
    expected = temp_home / '.config' / 'inkcut'
    assert config_home() == str(expected)
    assert _plugin('inkcut.job')._state_file == str(
        expected / 'inkcut.job.json')


def test_blank_config_variables_are_unset(temp_home, monkeypatch):
    monkeypatch.setenv('INKCUT_CONFIG_HOME', '   ')
    monkeypatch.setenv('XDG_CONFIG_HOME', '')
    assert config_home() == str(temp_home / '.config' / 'inkcut')


def test_config_home_follows_a_later_change(temp_home, monkeypatch):
    monkeypatch.setenv('INKCUT_CONFIG_HOME', str(temp_home / 'one'))
    assert config_home() == str(temp_home / 'one')
    monkeypatch.setenv('INKCUT_CONFIG_HOME', str(temp_home / 'two'))
    assert config_home() == str(temp_home / 'two')
    assert _plugin('inkcut.job')._state_file == str(
        temp_home / 'two' / 'inkcut.job.json')


def test_state_home_records_the_app_variable_without_a_suffix(
        temp_home, monkeypatch):
    chosen = temp_home / 'custom' / 'inkcut'
    monkeypatch.setenv('INKCUT_STATE_HOME', str(chosen))
    monkeypatch.setenv('XDG_STATE_HOME', str(temp_home / 'xdg-state'))
    assert state_home() == str(chosen)
    monkeypatch.setenv('INKCUT_STATE_HOME', str(temp_home / 'moved'))
    monkeypatch.setenv('XDG_STATE_HOME', str(temp_home / 'xdg-moved'))
    assert state_home() == str(chosen)
    assert log_dir() == os.path.join(str(chosen), 'logs')


def test_state_home_uses_xdg_once_then_keeps_that_path(
        temp_home, monkeypatch):
    xdg = temp_home / 'xdg-state'
    monkeypatch.setenv('XDG_STATE_HOME', str(xdg))
    assert state_home() == str(xdg / 'inkcut')
    monkeypatch.delenv('XDG_STATE_HOME')
    monkeypatch.setenv('INKCUT_STATE_HOME', str(temp_home / 'moved'))
    assert state_home() == str(xdg / 'inkcut')


def test_default_state_home_stays_when_variables_are_set_later(
        temp_home, monkeypatch):
    expected = str(temp_home / '.local' / 'state' / 'inkcut')
    assert state_home() == expected
    monkeypatch.setenv('INKCUT_STATE_HOME', str(temp_home / 'moved'))
    monkeypatch.setenv('XDG_STATE_HOME', str(temp_home / 'xdg-moved'))
    assert state_home() == expected
    record = (temp_home / '.config' / 'inkcut' / 'state-home').read_text()
    assert record.strip() == expected


def test_relative_state_home_is_recorded_as_an_absolute_path(
        temp_home, monkeypatch):
    monkeypatch.chdir(temp_home)
    monkeypatch.setenv('INKCUT_STATE_HOME', 'rel-state')
    recorded = state_home()
    assert recorded == str(temp_home / 'rel-state')
    other = temp_home / 'elsewhere'
    other.mkdir()
    monkeypatch.chdir(other)
    monkeypatch.setenv('INKCUT_STATE_HOME', 'other-rel')
    assert state_home() == recorded


def test_new_logs_use_the_state_home_and_leave_old_logs(temp_home):
    old_log = temp_home / '.config' / 'inkcut' / 'logs' / 'inkcut.txt'
    old_log.parent.mkdir(parents=True)
    old_log.write_text('keep\n')
    root = logging.getLogger()
    level = root.level
    handlers = list(root.handlers)
    from inkcut.app import init_logging
    try:
        init_logging()
        new_log = temp_home / '.local' / 'state' / 'inkcut' / 'logs' / 'inkcut.txt'
        assert new_log.is_file()
        assert old_log.read_text() == 'keep\n'
        assert not (temp_home / '.local' / 'share' / 'inkcut').exists()
        assert not (temp_home / '.cache' / 'inkcut').exists()
    finally:
        root.setLevel(level)
        for handler in list(root.handlers):
            if handler not in handlers:
                handler.close()
                root.removeHandler(handler)


def test_log_menu_opens_the_state_home(temp_home):
    import enaml
    with enaml.imports():
        from inkcut.ui.manifest import UIManifest
    manifest = UIManifest()
    urls = []
    for node in _walk(manifest):
        if getattr(node, 'path', None) == '/help/logs':
            urls.append(node.parameters['url'])
    expected = str(temp_home / '.local' / 'state' / 'inkcut' / 'logs') + os.sep
    assert urls == [expected]


def test_data_and_cache_homes_follow_the_same_rule(temp_home, monkeypatch):
    cases = (
        ('INKCUT_DATA_HOME', 'XDG_DATA_HOME', data_home,
         ('.local', 'share')),
        ('INKCUT_CACHE_HOME', 'XDG_CACHE_HOME', cache_home, ('.cache',)),
    )
    for app_var, xdg_var, resolver, default_parts in cases:
        chosen = temp_home / app_var
        monkeypatch.setenv(app_var, str(chosen))
        monkeypatch.setenv(xdg_var, str(temp_home / 'xdg'))
        assert resolver() == str(chosen)
        monkeypatch.delenv(app_var)
        assert resolver() == str(temp_home / 'xdg' / 'inkcut')
        monkeypatch.delenv(xdg_var)
        assert resolver() == str(temp_home.joinpath(*default_parts, 'inkcut'))
        assert not Path(resolver()).exists()


def test_runtime_dir_fails_when_unset_and_does_not_use_tmp(
        temp_home, monkeypatch):
    with pytest.raises(RuntimeError):
        runtime_dir()
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(temp_home / 'run'))
    assert runtime_dir() == str(temp_home / 'run' / 'inkcut')
    monkeypatch.setenv('INKCUT_RUNTIME_DIR', str(temp_home / 'app-run'))
    assert runtime_dir() == str(temp_home / 'app-run')


def test_only_the_resolver_reads_xdg_home_variables():
    root = Path(__file__).resolve().parents[1]
    resolver = root / 'inkcut' / 'core' / 'homes.py'
    skipped = {
        root / 'agents',
        root / 'tests',
        root / '.git',
        root / 'inkcut.egg-info',
    }
    offenders = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix not in ('.py', '.enaml'):
            continue
        if path == resolver or any(_is_under(path, parent) for parent in skipped):
            continue
        if '__pycache__' in path.parts or '__enamlcache__' in path.parts:
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        for name in _XDG_HOME_VARS:
            if name in text:
                offenders.append('{}: {}'.format(path, name))
    assert offenders == []


def _walk(node):
    yield node
    for child in getattr(node, 'children', ()) or ():
        yield from _walk(child)


def _is_under(path, parent):
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
