# -*- coding: utf-8 -*-
"""
Copyright (c) 2025, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Provides visual indicators for origin location and feed direction in the preview.

@author: AI Assistant
"""
from typing import Optional, Any
from enaml.qt import QtGui, QtCore
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject

import sys

print(sys.executable)


class OriginIndicator(GraphicsObject):
    """Visual indicator for the origin location with a dot and label."""

    def __init__(self,
                 x: float = 0,
                 y: float = 0,
                 origin_position: str = 'bottom_left',
                 parent: Optional[GraphicsObject] = None) -> None:
        """
        Initialize the origin indicator.

        Parameters
        ----------
        x : float
            X coordinate of the origin
        y : float
            Y coordinate of the origin
        origin_position : str
            One of: 'bottom_left', 'bottom_right', 'top_left', 'top_right'
        parent : QGraphicsItem
            Parent graphics item
        """
        super().__init__(parent)
        self.setX(x)
        self.setY(y)
        self.origin_position: str = origin_position
        self.dot_radius: int = 5
        self.label_offset: int = 15

        # Create pen for the dot
        self.pen: QtGui.QPen = QtGui.QPen(QtCore.Qt.GlobalColor.black, 2)
        self.brush: QtGui.QBrush = QtGui.QBrush(QtCore.Qt.GlobalColor.black)

        # Create font for the label
        self.font: QtGui.QFont = QtGui.QFont()
        self.font.setPointSize(10)
        self.font.setBold(True)

    def paint(self,
              painter: Optional[QtGui.QPainter],
              option: Optional[Any] = None,
              widget: Optional[Any] = None) -> None:
        """Paint the origin indicator."""

        if painter is None:
            return

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        # Draw the dot at origin
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawEllipse(QtCore.QPointF(self.x(), self.y()),
                            self.dot_radius, self.dot_radius)

        # Calculate label position based on origin_position
        # Label text dimensions (approximate)
        label_width: int = 60
        label_height: int = 20
        label_text: str = "Origin"

        # Position label so its bottom-right corner is offset from origin
        # The label should appear in the opposite quadrant from the design
        origin_x: float = self.x()
        origin_y: float = self.y()

        if self.origin_position == 'bottom_left':
            # Design is in quadrant I (up-right), label goes to quadrant III (down-left)
            # Bottom-right of label at (0 - offset, 0 - offset)
            label_right: float = origin_x - self.label_offset
            label_bottom: float = origin_y - self.label_offset
            label_x: float = label_right - label_width
            label_y: float = label_bottom - label_height
        elif self.origin_position == 'bottom_right':
            # Design is in quadrant II (up-left), label goes to quadrant IV (down-right)
            # Bottom-left of label at (0 + offset, 0 - offset)
            label_left: float = origin_x + self.label_offset
            label_bottom = origin_y - self.label_offset
            label_x = label_left
            label_y = label_bottom - label_height
        elif self.origin_position == 'top_left':
            # Design is in quadrant IV (down-right), label goes to quadrant II (up-left)
            # Top-right of label at (0 - offset, 0 + offset)
            label_right = origin_x - self.label_offset
            label_top: float = origin_y + self.label_offset
            label_x = label_right - label_width
            label_y = label_top
        elif self.origin_position == 'top_right':
            # Design is in quadrant III (down-left), label goes to quadrant I (up-right)
            # Top-left of label at (0 + offset, 0 + offset)
            label_left = origin_x + self.label_offset
            label_top = origin_y + self.label_offset
            label_x = label_left
            label_y = label_top
        else:
            label_x = origin_x
            label_y = origin_y

        # Draw the label with proper orientation
        # Save painter state to preserve current transformation
        painter.save()

        # Apply Y-flip correction to counteract the preview's coordinate system flip
        painter.translate(label_x, label_y)
        painter.scale(1, -1)
        painter.translate(-label_x, -label_y)

        # Draw the label
        painter.setFont(self.font)
        painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black, 1))
        painter.drawText(
            QtCore.QRectF(label_x, label_y, label_width, label_height),
            QtCore.Qt.AlignmentFlag.AlignCenter, label_text)

        # Restore painter state
        painter.restore()

    def boundingRect(self) -> QtCore.QRectF:
        """Return the bounding rectangle."""
        margin: int = 80
        origin_x: float = self.x()
        origin_y: float = self.y()
        return QtCore.QRectF(origin_x - margin, origin_y - margin, margin * 2,
                             margin * 2)


class FeedDirectionIndicator(GraphicsObject):
    """Visual indicator for the feed direction with arrow and label."""

    def __init__(self,
                 x: float = 0,
                 y: float = 0,
                 feed_axis: str = 'y',
                 origin_position: str = 'bottom_left',
                 material_width: float = 100,
                 material_height: float = 100,
                 parent: Optional[GraphicsObject] = None) -> None:
        """
        Initialize the feed direction indicator.

        Parameters
        ----------
        x : float
            X coordinate for the indicator
        y : float
            Y coordinate for the indicator
        feed_axis : str
            Either 'x' or 'y' for the feed direction
        origin_position : str
            One of: 'bottom_left', 'bottom_right', 'top_left', 'top_right'
        material_width : float
            Width of the material (for positioning)
        material_height : float
            Height of the material (for positioning)
        parent : QGraphicsItem
            Parent graphics item
        """
        super().__init__(parent)
        self.setX(x)
        self.setY(y)
        self.feed_axis: str = feed_axis.lower()
        self.origin_position: str = origin_position
        self.material_width: float = material_width
        self.material_height: float = material_height
        self.arrow_length: int = 10 * 5  # ~10 character widths (5 pixels per char)
        self.label_offset: int = 15

        # Create pen for the arrow
        self.pen: QtGui.QPen = QtGui.QPen(QtCore.Qt.GlobalColor.blue, 2)
        self.pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        self.pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)

        # Create font for the label
        self.font: QtGui.QFont = QtGui.QFont()
        self.font.setPointSize(12)
        self.font.setBold(True)

    def _get_feed_direction(self) -> str:
        """
        Determine the actual feed direction based on feed_axis and origin_position.

        Returns
        -------
        direction : str
            One of: 'left', 'right', 'up', 'down'
        """
        if self.feed_axis == 'x':
            # X-axis feed direction
            if self.origin_position in ('bottom_left', 'top_left'):
                return 'left'
            else:  # bottom_right, top_right
                return 'right'
        else:  # feed_axis == 'y'
            # Y-axis feed direction
            if self.origin_position in ('bottom_left', 'bottom_right'):
                return 'down'
            else:  # top_left, top_right
                return 'up'

    def paint(self,
              painter: Optional[QtGui.QPainter],
              option: Optional[Any] = None,
              widget: Optional[Any] = None) -> None:
        """Paint the feed direction indicator."""

        if painter is None:
            return

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(self.pen)

        direction: str = self._get_feed_direction()
        label: str = "Material Feed"
        label_width: int = 100
        label_height: int = 20

        # Position the indicator based on feed axis and origin
        # Arrow starts at origin and points in feed direction
        label_x: float = 0
        label_y: float = 0
        origin_x: float = self.x()
        origin_y: float = self.y()

        if self.feed_axis == 'x':
            # Horizontal feed - arrow on X axis
            arrow_y: float = origin_y

            if direction == 'left':
                # Arrow pointing left from origin
                arrow_start_x: float = origin_x
                arrow_end_x: float = origin_x - self.arrow_length
                arrow_y = origin_y

                # Draw arrow line
                painter.drawLine(int(arrow_start_x), int(arrow_y),
                                 int(arrow_end_x), int(arrow_y))

                # Draw arrowhead
                arrow_size: int = 5
                painter.drawLine(int(arrow_end_x), int(arrow_y),
                                 int(arrow_end_x + arrow_size),
                                 int(arrow_y - arrow_size))
                painter.drawLine(int(arrow_end_x), int(arrow_y),
                                 int(arrow_end_x + arrow_size),
                                 int(arrow_y + arrow_size))

                # Label positioning based on origin_position
                if self.origin_position == 'bottom_left':
                    # Label ABOVE arrow in Q II
                    # Top-right of label at origin + offset
                    label_right: float = origin_x + self.label_offset
                    label_top: float = origin_y + self.label_offset
                    label_x = label_right - label_width
                    label_y = label_top
                elif self.origin_position == 'top_left':
                    # Label BELOW arrow in Q III
                    # Bottom-right of label at origin - offset
                    label_right = origin_x + self.label_offset
                    label_bottom: float = origin_y - self.label_offset
                    label_x = label_right - label_width
                    label_y = label_bottom - label_height

            else:  # right
                # Arrow pointing right from origin
                arrow_start_x = origin_x
                arrow_end_x = origin_x + self.arrow_length
                arrow_y = origin_y

                # Draw arrow line
                painter.drawLine(int(arrow_start_x), int(arrow_y),
                                 int(arrow_end_x), int(arrow_y))

                # Draw arrowhead
                arrow_size = 5
                painter.drawLine(int(arrow_end_x), int(arrow_y),
                                 int(arrow_end_x - arrow_size),
                                 int(arrow_y - arrow_size))
                painter.drawLine(int(arrow_end_x), int(arrow_y),
                                 int(arrow_end_x - arrow_size),
                                 int(arrow_y + arrow_size))

                # Label positioning based on origin_position
                if self.origin_position == 'bottom_right':
                    # Label ABOVE arrow in Q I
                    # Top-left of label at origin + offset
                    label_left: float = origin_x + self.label_offset
                    label_top = origin_y + self.label_offset
                    label_x = label_left
                    label_y = label_top
                elif self.origin_position == 'top_right':
                    # Label BELOW arrow in Q IV
                    # Bottom-left of label at origin - offset
                    label_left = origin_x + self.label_offset
                    label_bottom = origin_y - self.label_offset
                    label_x = label_left
                    label_y = label_bottom - label_height

        else:  # feed_axis == 'y'
            # Vertical feed - arrow on Y axis
            arrow_x: float = origin_x

            if direction == 'up':
                # Arrow pointing up from origin
                arrow_start_y: float = origin_y
                arrow_end_y: float = origin_y + self.arrow_length
                arrow_x = origin_x

                # Draw arrow line
                painter.drawLine(int(arrow_x), int(arrow_start_y),
                                 int(arrow_x), int(arrow_end_y))

                # Draw arrowhead
                arrow_size = 5
                painter.drawLine(int(arrow_x), int(arrow_end_y),
                                 int(arrow_x - arrow_size),
                                 int(arrow_end_y - arrow_size))
                painter.drawLine(int(arrow_x), int(arrow_end_y),
                                 int(arrow_x + arrow_size),
                                 int(arrow_end_y - arrow_size))

                # Label positioning based on origin_position
                if self.origin_position == 'top_right':
                    # Label LEFT of arrow in Q II
                    # Top-right of label at origin - offset
                    label_right = origin_x - self.label_offset
                    label_top = origin_y + self.label_offset
                    label_x = label_right - label_width
                    label_y = label_top
                elif self.origin_position == 'top_left':
                    # Label RIGHT of arrow in Q I
                    # Top-left of label at origin + offset
                    label_left = origin_x + self.label_offset
                    label_top = origin_y + self.label_offset
                    label_x = label_left
                    label_y = label_top

            else:  # down
                # Arrow pointing down from origin
                arrow_start_y = origin_y
                arrow_end_y = origin_y - self.arrow_length
                arrow_x = origin_x

                # Draw arrow line
                painter.drawLine(int(arrow_x), int(arrow_start_y),
                                 int(arrow_x), int(arrow_end_y))

                # Draw arrowhead
                arrow_size = 5
                painter.drawLine(int(arrow_x), int(arrow_end_y),
                                 int(arrow_x - arrow_size),
                                 int(arrow_end_y + arrow_size))
                painter.drawLine(int(arrow_x), int(arrow_end_y),
                                 int(arrow_x + arrow_size),
                                 int(arrow_end_y + arrow_size))

                # Label positioning based on origin_position
                if self.origin_position == 'bottom_left':
                    # Label RIGHT of arrow in Q IV
                    # Bottom-left of label at origin - offset
                    label_left = origin_x + self.label_offset
                    label_bottom = origin_y - self.label_offset
                    label_x = label_left
                    label_y = label_bottom - label_height
                elif self.origin_position == 'bottom_right':
                    # Label LEFT of arrow in Q III
                    # Bottom-right of label at origin - offset
                    label_right = origin_x - self.label_offset
                    label_bottom = origin_y - self.label_offset
                    label_x = label_right - label_width
                    label_y = label_bottom - label_height

        # Draw the label with proper orientation
        # Save painter state to preserve current transformation
        painter.save()

        # Apply Y-flip correction to counteract the preview's coordinate system flip
        painter.translate(label_x, label_y)
        painter.scale(1, -1)
        painter.translate(-label_x, -label_y)

        # Draw the label with adequate space
        painter.setFont(self.font)
        painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.blue, 1))
        painter.drawText(
            QtCore.QRectF(label_x, label_y, label_width, label_height),
            QtCore.Qt.AlignmentFlag.AlignCenter, label)

        # Restore painter state
        painter.restore()

    def boundingRect(self) -> QtCore.QRectF:
        """Return the bounding rectangle."""
        margin: int = self.arrow_length + 100
        origin_x: float = self.x()
        origin_y: float = self.y()
        return QtCore.QRectF(origin_x - margin, origin_y - margin,
                             self.material_width + margin * 2,
                             self.material_height + margin * 2)
