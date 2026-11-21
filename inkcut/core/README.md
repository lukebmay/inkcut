# Core

- `__init__.py` marks the `inkcut.core` package and exports nothing.
- `api.py` re-exports the models, dock widgets, unit helpers, logger,
  and SVG module other code imports from core.
- `declarative.py` owns the Enaml declarative whose saved state keeps
  only its final declarative members.
- `homes.py` resolves the config, data, cache, runtime, state, and log
  directories from the Inkcut and XDG home variables.
- `manifest.enaml` registers the core plugin and the application,
  window, workspace, and menu extensions that start the UI.
- `models.py` owns the persisted Atom model, the padded work area, and
  the plugin base that saves config-tagged state.
- `plugin.py` owns the core plugin that starts logging, loads the CLI,
  and opens the default workspace.
- `svg.py` parses SVG documents into Qt painter paths in Inkcut's
  internal units.
- `utils.py` owns the shared logger, icon loaders, unit conversion,
  async sleep, painter-path helpers, and subclass lookup.
- `widgets.py` owns the dock item and dock area whose saved state is
  the layout the UI restores.
- `workbench.py` owns the workbench that prepares Qt, loads the core
  manifests, and runs the application.
