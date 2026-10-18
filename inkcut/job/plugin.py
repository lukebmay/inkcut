"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import sys
import enaml
from atom.api import Instance, Enum, List, Str, Int, Float, observe, Bool
from inkcut.core.api import Plugin, unit_conversions, log

from inkcut.device.plugin import orient_bed
from inkcut.preview.markers import cut_overlay, placed_origin

from .models import Job, JobError, Material

with enaml.imports():
    from enaml.workbench.ui.workbench_menus import WorkbenchMenu
    from .menu import RecentDocumentsMenu


def _has_line(path):
    for index in range(path.elementCount()):
        if path.elementAt(index).isLineTo():
            return True
    return False


def _append_cut_layers(view_items, path, plot, head, feed_direction, origin_side):
    """ Draw the cut. Return the start line, finish line, and marks.

    Those three are added after the material so the border does not cover them.
    """
    middle, approach, finish, marks = cut_overlay(
        path, head, feed_direction, origin_side)
    if _has_line(middle):
        view_items.append(dict(path=middle, pen=plot.pen_up))
    view_items.append(dict(path=path, pen=plot.pen_down))
    start = dict(path=approach, pen=plot.pen_start) if _has_line(approach) else None
    end = dict(path=finish, pen=plot.pen_end) if _has_line(finish) else None
    return start, end, marks


def _extend_overlay(view_items, overlay):
    for item in overlay:
        if item is not None:
            view_items.append(item)


class JobPlugin(Plugin):
    #: Units
    units = Enum(*unit_conversions.keys()).tag(config=True)

    #: Available materials
    materials = List(Material).tag(config=True)

    #: Current material
    material = Instance(Material, ()).tag(config=True)

    #: Previous jobs
    jobs = List(Job).tag(config=True)

    #: Current job
    job = Instance(Job).tag(config=True)

    #: Recently open paths
    recent_documents = List(Str()).tag(config=True)

    #: Number of recent documents
    recent_document_limit = Int(10).tag(config=True)
    saved_jobs_limit = Int(100).tag(config=True)

    #: Timeout for optimizing paths
    optimizer_timeout = Float(10, strict=False).tag(config=True)

    # Default DPI setting if no units are specified in document.
    dpi_default = Float(96, strict=False).tag(config=True)

    # Whether or not to auto-detect DPI settings for Inkscape SVG files.
    dpi_auto_detect_inkscape = Bool(True).tag(config=True)

    def _default_job(self):
        return Job(material=self.material)

    def _default_units(self):
        return "in"

    # -------------------------------------------------------------------------
    # Plugin API
    # -------------------------------------------------------------------------
    def start(self):
        """Register the plugins this plugin depends on"""
        #: Now load state
        super(JobPlugin, self).start()

        #: If we loaded from state, refresh
        if self.job.document:
            self.refresh_preview()

        self.init_recent_documents_menu()

    # -------------------------------------------------------------------------
    # Job API
    # -------------------------------------------------------------------------
    def request_approval(self, job):
        """Request approval to start a job. This will set the job.info.status
        to either 'approved' or 'cancelled'.

        """
        ui = self.workbench.get_plugin("enaml.workbench.ui")
        with enaml.imports():
            from .dialogs import JobApprovalDialog
        JobApprovalDialog(ui.window, plugin=self, job=job).exec_()

    def refresh_preview(self):
        """Refresh the preview. Other plugins can request this"""
        self._refresh_preview({})

    def can_open(self, url):
        """Check if the given source url can be opened"""
        result = False
        try:
            if url:
                schema, path = url.split("://")
                if schema == "file" and os.path.exists(path):
                    result = path.endswith(".svg")
        except Exception as e:
            log.exception(e)
        # log.debug("Checking if {} can be opened... {}".format(url, result))
        return result

    def open_document(self, path, nodes=None):
        """Set the job.document if it is empty, otherwise close and create
        a  new Job instance.

        """
        if path == "-":
            log.debug("Opening document from stdin...")
            from_source = True
        elif path.startswith("<?xml"):
            log.debug("Opening document from source...")
            from_source = True
        elif not os.path.exists(path):
            raise JobError("Cannot open %s, it does not exist!" % path)
        elif not os.path.isfile(path):
            raise JobError("Cannot open %s, it is not a file!" % path)
        else:
            from_source = False

        # Close any old docs
        self.close_document()

        try:
            log.info("Opening {doc}".format(doc=path[:200]))
            job = self.job
            job.document_kwargs = dict(ids=nodes)
            job.document = path
        except ValueError as e:
            #: Wrap in a JobError
            raise JobError(e)

        # Update recent documents
        if not from_source:
            docs = self.recent_documents[:]
            # Remove and re-ad to make it most recent
            if path in docs:
                docs.remove(path)
            docs.append(path)

            # Keep limit to 10
            if len(docs) > 10:
                docs.pop(0)

            self.recent_documents = docs

    def save_document(self):
        # Copy so the ui's update
        job = self.job
        jobs = self.jobs[:]
        if job in jobs:
            # Save a copy or any changes will update the copy as well
            job = job.clone()
        jobs.append(job)

        # Limit size
        if len(jobs) > self.saved_jobs_limit:
            jobs.pop(0)

        self.jobs = jobs

    def close_document(self):
        """If the job currently has a "document" add this to the jobs list
        and create a new Job instance. Otherwise no job is open so do nothing.

        """
        if not self.job.document:
            return

        log.info("Closing {doc}".format(doc=self.job))
        # Create a new default job
        self.job = self._default_job()

    @observe("job.material")
    def _observe_material(self, change):
        """Keep the job material and plugin material in sync."""
        m = self.material
        job = self.job
        if job.material != m:
            job.material = m

    @observe("job", "job.model", "job.material", "material.size", "material.padding")
    def _refresh_preview(self, change):
        """Redraw the preview on the screen"""
        log.info(change)
        view_items = []
        overlay = []

        preview_plugin = self.workbench.get_plugin("inkcut.preview")
        job = self.job
        plot = preview_plugin.preview

        #: Draw the device
        plugin = self.workbench.get_plugin("inkcut.device")
        device = plugin.device

        if device:
            scale = device.output_scale()
            feed_direction = device.config.feed_direction
            origin_side = device.config.origin_side
            if device.area:
                view_items.append(
                    dict(
                        path=orient_bed(
                            device.area.path, feed_direction, origin_side, scale
                        ),
                        pen=plot.pen_device,
                        skip_autorange=True,
                    )
                )
            output = device.preview_output_path(job)
            if output is not None:
                overlay.extend(_append_cut_layers(
                    view_items, output, plot,
                    placed_origin(device, job), feed_direction, origin_side,
                ))
            if job.material:
                view_items.extend(
                    [
                        dict(
                            path=orient_bed(
                                job.material.path, feed_direction, origin_side,
                                scale,
                            ),
                            pen=plot.pen_media,
                            skip_autorange=([0, job.size[0]], [0, job.size[1]]),
                        ),
                        dict(
                            path=orient_bed(
                                job.material.padding_path, feed_direction,
                                origin_side, scale,
                            ),
                            pen=plot.pen_media_padding,
                            skip_autorange=True,
                        ),
                    ]
                )
        else:
            # No device yet: draw the job model as it stands.
            t = preview_plugin.transform
            if job.model:
                overlay.extend(_append_cut_layers(
                    view_items, job.model, plot, (0.0, 0.0), "down", "left",
                ))
            if job.material:
                view_items.extend(
                    [
                        dict(
                            path=t.map(job.material.path),
                            pen=plot.pen_media,
                            skip_autorange=([0, job.size[0]], [0, job.size[1]]),
                        ),
                        dict(
                            path=t.map(job.material.padding_path),
                            pen=plot.pen_media_padding,
                            skip_autorange=True,
                        ),
                    ]
                )

        _extend_overlay(view_items, overlay)

        #: Update the plot
        preview_plugin.set_preview(*view_items)

        #: Save config
        self.save()

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def init_recent_documents_menu(self):
        """Insert the `RecentDocumentsMenu` into the Menu declaration that
        automatically updates the recent document menu links.

        """
        recent_menu = self.get_recent_menu()
        if recent_menu is None:
            return
        for c in recent_menu.children:
            if isinstance(c, RecentDocumentsMenu):
                return  # Already added
        documents_menu = RecentDocumentsMenu(plugin=self, parent=recent_menu)
        documents_menu.initialize()

    def get_recent_menu(self):
        """Get the recent menu item WorkbenchMenu"""
        ui = self.workbench.get_plugin("enaml.workbench.ui")
        window_model = ui._model
        if not window_model:
            return
        for menu in window_model.menus:
            if menu.item.path == "/file":
                for c in menu.children:
                    if isinstance(c, WorkbenchMenu):
                        if c.item.path == "/file/recent/":
                            return c
