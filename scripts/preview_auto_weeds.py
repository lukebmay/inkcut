#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render keep + weed paths for auto peel (preview-like SVG).

Usage:
  PYTHONPATH=. python3 scripts/preview_auto_weeds.py
  PYTHONPATH=. python3 scripts/preview_auto_weeds.py --out /tmp/weeds.svg

Writes SVG with keep (black) and weeds (orange) for visual check without GUI.
"""
from __future__ import division, print_function

import argparse
import math
import os
import sys

# Offscreen Qt
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath
from enaml.qt.QtWidgets import QApplication

if QApplication.instance() is None:
    QApplication([])

from inkcut.job.weeds import (
    auto_weeds, frame_weeds, generate_weeds, grid_weeds, region_weeds,
    weed_path_stats,
)


def rect_path(x, y, w, h):
    p = QPainterPath()
    p.addRect(QRectF(x, y, w, h))
    return p


def circle_path(cx, cy, r):
    p = QPainterPath()
    p.addEllipse(QPointF(cx, cy), r, r)
    return p


def diamond_path():
    p = QPainterPath()
    p.moveTo(50, 5)
    p.lineTo(80, 50)
    p.lineTo(50, 95)
    p.lineTo(20, 50)
    p.closeSubpath()
    return p


def nested_logo():
    p = QPainterPath()
    p.addPath(circle_path(50, 50, 40))
    p.addPath(rect_path(38, 38, 24, 24))
    return p


def two_islands():
    p = QPainterPath()
    p.addPath(rect_path(10, 30, 25, 40))
    p.addPath(rect_path(45, 30, 25, 40))
    return p


def path_to_svg_d(path):
    """Convert QPainterPath to SVG path d (lines only)."""
    parts = []
    for i in range(path.elementCount()):
        e = path.elementAt(i)
        if e.isMoveTo():
            parts.append('M %.3f %.3f' % (e.x, e.y))
        elif e.isLineTo():
            parts.append('L %.3f %.3f' % (e.x, e.y))
        else:
            # curve → line to end
            parts.append('L %.3f %.3f' % (e.x, e.y))
    return ' '.join(parts)


def render_case(name, keep, modes, padding, spacing, out_dir):
    br = keep.boundingRect()
    pad = max(padding) if padding else 10
    margin = pad + 5
    vb_x = br.x() - margin
    vb_y = br.y() - margin
    vb_w = br.width() + 2 * margin
    vb_h = br.height() + 2 * margin

    panels = []
    x_off = 0
    gap = 15
    for mode in modes:
        weed = generate_weeds(
            keep, mode=mode, padding=padding, spacing=spacing)
        st = weed_path_stats(weed)
        panels.append((mode, weed, st, x_off))
        x_off += vb_w + gap

    total_w = x_off - gap
    total_h = vb_h + 28
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="%.1f" height="%.1f" viewBox="0 0 %.1f %.1f">' % (
            total_w, total_h, total_w, total_h),
        '<rect width="100%" height="100%" fill="#fafafa"/>',
        '<text x="4" y="14" font-family="sans-serif" font-size="11" '
        'fill="#333">%s (black=keep, orange=weed)</text>' % name,
    ]
    y0 = 22
    for mode, weed, st, xo in panels:
        lines.append(
            '<g transform="translate(%.1f,%.1f)">' % (xo, y0))
        lines.append(
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
            'fill="#fff" stroke="#ddd"/>' % (0, 0, vb_w, vb_h))
        # shift content
        lines.append(
            '<g transform="translate(%.1f,%.1f)">' % (-vb_x, -vb_y))
        kd = path_to_svg_d(keep)
        wd = path_to_svg_d(weed)
        if kd:
            lines.append(
                '<path d="%s" fill="none" stroke="#222" '
                'stroke-width="1.2"/>' % kd)
        if wd:
            lines.append(
                '<path d="%s" fill="none" stroke="#e67e22" '
                'stroke-width="1.0"/>' % wd)
        lines.append('</g>')
        lines.append(
            '<text x="4" y="%.1f" font-family="sans-serif" font-size="10" '
            'fill="#555">%s · segs=%d len=%.0f</text>' % (
                vb_h - 4, mode, st['segments'], st['length']))
        lines.append('</g>')

    lines.append('</svg>')
    path = os.path.join(out_dir, 'weed_%s.svg' % name)
    with open(path, 'w') as f:
        f.write('\n'.join(lines))
    print('wrote', path)
    for mode, weed, st, _ in panels:
        print('  %s: segments=%d length=%.1f' % (
            mode, st['segments'], st['length']))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        '--out-dir', default=os.path.join(
            os.path.dirname(__file__), '..', 'tests', 'data', 'weed_preview'),
        help='Directory for SVG previews')
    args = ap.parse_args(argv)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    pad = [12, 12, 12, 12]
    modes = ['frame', 'grid', 'region', 'auto']
    cases = [
        ('rect', rect_path(20, 20, 60, 40), 15),
        ('nested', nested_logo(), 15),
        ('diamond', diamond_path(), 20),
        ('two_islands', two_islands(), 15),
    ]
    for name, keep, spacing in cases:
        render_case(name, keep, modes, pad, spacing, out_dir)
    print('done →', out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
