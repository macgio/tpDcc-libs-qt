#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt slider widgets
"""

from __future__ import print_function, division, absolute_import

from copy import copy

from Qt.QtCore import *
from Qt.QtGui import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import mathlib, color as core_color
from tpDcc.libs.qt.core import qtutils, color, mixin

FLOAT_SLIDER_DRAG_STEPS = [100.0, 10.0, 1.0, 0.1, 0.01, 0.001]
INT_SLIDER_DRAG_STEPS = [100.0, 10.0, 1.0]


@mixin.theme_mixin
class BaseSlider(QSlider, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(BaseSlider, self).__init__(orientation, parent=parent)

    def mouseMoveEvent(self, event):
        QToolTip.showText(event.globalPos(), str(self.value()), self)
        return super(BaseSlider, self).mouseMoveEvent(event)


class SliderDraggers(QWidget, object):
    increment = Signal(object)

    def __init__(self, parent=None, is_float=True, dragger_steps=None, main_color=None):
        super(SliderDraggers, self).__init__(parent)

        self._drags = list()
        self._initial_pos = None
        self._active_drag = None
        self._last_delta_x = 0
        self._change_direction = 0
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
        dragger_steps = dragger_steps or FLOAT_SLIDER_DRAG_STEPS

        self.setWindowFlags(Qt.Popup)

        draggers_layout = QVBoxLayout()
        draggers_layout.setContentsMargins(0, 0, 0, 0)
        draggers_layout.setSpacing(0)
        self.setLayout(draggers_layout)

        steps = copy(dragger_steps)
        if not is_float:
            steps = list(filter(lambda x: abs(x) >= 1.0, steps))
        for i in steps:
            drag = HoudiniInputDragger(self, i)
            self._drags.append(drag)
            draggers_layout.addWidget(drag)

        self.installEventFilter(self)

    @property
    def active_drag(self):
        return self._active_drag

    @active_drag.setter
    def active_drag(self, input_dragger):
        self._active_drag = input_dragger

    @property
    def drags(self):
        return self._drags

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            if self._active_drag:
                modifiers = event.modifiers()
                self._active_drag.setStyleSheet(self._get_style_sheet())
                if not self._initial_pos:
                    self._initial_pos = event.globalPos()
                delta_x = event.globalPos().x() - self._initial_pos.x()
                self._change_direction = mathlib.clamp(delta_x - self._last_delta_x, -1.0, 1.0)
                if self._change_direction != 0:
                    v = self._change_direction * self._active_drag.factor
                    if modifiers == Qt.NoModifier and delta_x % 4 == 0:
                        self.increment.emit(v)
                    if modifiers in [Qt.ShiftModifier, Qt.ControlModifier] and delta_x % 8 == 0:
                        self.increment.emit(v)
                    if modifiers == Qt.ShiftModifier | Qt.ControlModifier and delta_x % 32 == 0:
                        self.increment.emit(v)
                self._last_delta_x = delta_x
        if event.type() == QEvent.MouseButtonRelease:
            self.hide()
            self._last_delta_x = 0
            del(self)

        return False

    def _get_style_sheet(self):
        return """
        QGroupBox{
            border: 0.5 solid darkgrey;
            background : %s;
            color: white;
        }
        QLabel{
            background: transparent;
            border: 0 solid transparent;
            color: white;
        }
        """ % "rgba%s" % str(self._main_color)


class Slider(QSlider, object):
    """
    Custom slider that allows:
    - Left/Mid: Click to move handle
    - Ctrl and drag to move handle half velocity
    - Shift and drag to move handle quarter velocity
    - Ctrl + Shift and drag to move handle eighty velocity
    """

    editingFinihsed = Signal()
    valueIncremented = Signal(object)
    floatValueChanged = Signal(object)

    def __init__(self, parent=None, dragger_steps=None, slider_range=None, *args, **kwargs):
        if dragger_steps is None:
            dragger_steps = INT_SLIDER_DRAG_STEPS
        if slider_range is None:
            slider_range = [-100, 100]
        super(Slider, self).__init__(parent=parent, **kwargs)

        self._slider_range = slider_range
        self._dragger_steps = dragger_steps
        self._is_float = False
        self._default_value = 0
        self._prev_value = 0
        self._delta_value = 0
        self._start_drag_pos = QPointF()
        self._real_start_drag_pos = QPointF()
        self._draggers = None

        if tp.is_maya():
            self._left_button = Qt.MidButton
            self._mid_button = Qt.LeftButton
        else:
            self._left_button = Qt.LeftButton
            self._mid_button = Qt.MidButton

        self.setFocusPolicy(Qt.StrongFocus)
        self.setOrientation(Qt.Horizontal)
        self.setRange(self._slider_range[0], self._slider_range[1])

    def mousePressEvent(self, event):
        self._prev_value = self.value()
        self._start_drag_pos = event.pos()
        if event.button() == Qt.MidButton:
            if not self._draggers:
                self._draggers = SliderDraggers(parent=self, is_float=self._is_float, dragger_steps=self._dragger_steps)
                self._draggers.increment.connect(self.valueIncremented.emit)
            self._draggers.show()
            if self._is_float:
                self._draggers.move(
                    self.mapToGlobal(QPoint(event.pos().x() - 1, event.pos().y() - self._draggers.height() / 2)))
            else:
                draggers_height = self._draggers.height()
                self._draggers.move(
                    self.mapToGlobal(
                        QPoint(event.pos().x() - 1, event.pos().y() - (self._draggers.height() - draggers_height / 6))))
        elif event.button() == self._left_button and event.modifiers() not in \
                [Qt.ControlModifier, Qt.ShiftModifier, Qt.ControlModifier | Qt.ShiftModifier]:
            buttons = Qt.MouseButtons(self._mid_button)
            mouse_event = QMouseEvent(event.type(), event.pos(), self._mid_button, buttons, event.modifiers())
            super(Slider, self).mousePressEvent(mouse_event)
        elif event.modifiers() in [Qt.ControlModifier, Qt.ShiftModifier, Qt.ControlModifier | Qt.ShiftModifier]:
            style_slider = QStyleOptionSlider()
            style_slider.initFrom(self)
            style_slider.orientation = self.orientation()
            available = self.style().pixelMetric(QStyle.PM_SliderSpaceAvailable, style_slider, self)
            x_loc = QStyle.sliderPositionFromValue(
                self.minimum(), self.maximum(), super(Slider, self).value(), available)
            buttons = Qt.MouseButtons(self._mid_button)
            new_pos = QPointF()
            new_pos.setX(x_loc)
            mouse_event = QMouseEvent(event.type(), new_pos, self._mid_button, buttons, event.modifiers())
            self._start_drag_pos = new_pos
            self._real_start_drag_pos = event.pos()
            super(Slider, self).mousePressEvent(mouse_event)
            self._delta_value = self.value() - self._prev_value
            self.setValue(self._prev_value)
        else:
            super(Slider, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        delta_x = event.pos().x() - self._real_start_drag_pos.x()
        delta_y = event.pos().y() - self._real_start_drag_pos.y()
        new_pos = QPointF()
        if event.modifiers() in [Qt.ControlModifier, Qt.ShiftModifier, Qt.ControlModifier | Qt.ShiftModifier]:
            if event.modifiers() == Qt.ControlModifier:
                new_pos.setX(self.startDragpos.x() + delta_x / 2)
                new_pos.setY(self.startDragpos.y() + delta_y / 2)
            elif event.modifiers() == Qt.ShiftModifier:
                new_pos.setX(self.startDragpos.x() + delta_x / 4)
                new_pos.setY(self.startDragpos.y() + delta_y / 4)
            elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier:
                new_pos.setX(self.startDragpos.x() + delta_x / 8)
                new_pos.setY(self.startDragpos.y() + delta_y / 8)
            mouse_event = QMouseEvent(event.type(), new_pos, event.button(), event.buttons(), event.modifiers())
            super(Slider, self).mouseMoveEvent(mouse_event)
            self.setValue(self.value() - self._delta_value)
        else:
            super(Slider, self).mouseMoveEvent(event)

    def keyPressEvent(self, event):
        p = self.mapFromGlobal(QCursor.pos())
        self._start_drag_pos = p
        self._real_start_drag_pos = p
        self._default_value = 0
        super(Slider, self).keyPressEvent(event)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super(Slider, self).wheelEvent(event)

    @property
    def slider_range(self):
        return self._slider_range


class DoubleSlider(Slider, object):
    doubleValueChanged = Signal(float)

    def __init__(self, parent=None, slider_range=None, default_value=0.0, maximum_value=1000000, dragger_steps=None):
        if slider_range is None:
            slider_range = (-100.0, 100.0)
        if dragger_steps is None:
            dragger_steps = FLOAT_SLIDER_DRAG_STEPS
        super(DoubleSlider, self).__init__(parent=parent, dragger_steps=dragger_steps, slider_range=slider_range)

        self._is_float = True
        self._maximum_value = abs(maximum_value)

        self.setOrientation(Qt.Horizontal)
        self.setMinimum(0)
        self.setMaximum(self._maximum_value)

        self.valueChanged.connect(self._on_value_changed)
        self.valueIncremented.connect(self._on_value_incremented)
        self.set_mapped_value(default_value, True)

    def mapped_value(self):
        return self._map_value(self.value())

    def set_mapped_value(self, value, block_signals=False):
        internal_value = self._unmap_value(value)
        if block_signals:
            self.blockSignals(True)
        self.setValue(internal_value)
        if self.signalsBlocked() and block_signals:
            self.blockSignals(False)

    def _map_value(self, in_value):
        """
        Internal function that converts slider integer value to slider float range value
        :param in_value:
        :return:
        """

        return mathlib.map_range_unclamped(
            in_value, self.minimum(), self.maximum(), self._slider_range[0], self._slider_range[1])

    def _unmap_value(self, out_value):
        """
        Converts mapped float value to slider integer value
        :param out_value:
        :return:
        """

        return int(mathlib.map_range_unclamped(
            out_value, self._slider_range[0], self._slider_range[1], self.minimum(), self.maximum()))

    def _on_value_changed(self, x):
        mapped_value = self._map_value(x)
        self.doubleValueChanged.emit(mapped_value)

    def _on_value_incremented(self, step):
        slider_internal_range = (self.minimum(), self.maximum())
        slider_dst = max(slider_internal_range) - min(slider_internal_range)
        value_dst = max(self._slider_range) - min(self._slider_range)
        factor = slider_dst / value_dst
        unmapped_step = step * factor
        current_internal_value = self.value()
        new_unmapped_value = current_internal_value + unmapped_step
        self.setValue(new_unmapped_value)


class HoudiniInputDragger(QWidget, object):
    """
    Widget that allow to drag values when mid click over widget.
    Right Drag increments values and Left Drag decreases value
    """

    def __init__(self, parent, factor, main_color=None, *args, **kwargs):
        super(HoudiniInputDragger, self).__init__(*args, **kwargs)

        self._parent = parent
        self._factor = factor
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
        self._size = 35

        self.setAttribute(Qt.WA_Hover)
        self.setStyleSheet(self._get_style_sheet())
        self.setMinimumHeight(self._size)
        self.setMinimumWidth(self._size)
        self.setMaximumHeight(self._size)
        self.setMaximumWidth(self._size)

        main_layout = QVBoxLayout()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        self._frame = QGroupBox()
        self._frame.setLayout(frame_layout)
        main_layout.addWidget(self._frame)

        self._label = QLabel('+' + str(factor))
        font = self._label.font()
        font.setPointSize(7)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self._label)

        self.installEventFilter(self)
        self._label.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            self.setStyleSheet(self._get_style_sheet(hover_style=True))
            self._parent.active_drag = self
            for drag in self._parent.drags:
                if drag != self:
                    drag.setStyleSheet(self._get_style_sheet())
        if event.type() == QEvent.HoverLeave:
            if event.pos().y() > self.height() or event.pos().y() < 0:
                self.setStyleSheet(self._get_style_sheet())
        if event.type() == QEvent.MouseMove:
            self._parent.eventFilter(self, event)

        return False

    @property
    def factor(self):
        return self._factor

    def _get_style_sheet(self, hover_style=False):
        if hover_style:
            return """
            QGroupBox{
                border: 0.5 solid darkgrey;
                background : %s;
                color: white;
            }
            QLabel{
                background: transparent;
                border: 0 solid transparent;
                color: white;
            }
            """ % "rgba%s" % str(self._main_color)
        else:
            return """
            QGroupBox{
                border: 0.5 solid darkgrey;
                background : black;
                color: white;
            }
            QLabel{
                background: transparent;
                border: 0 solid transparent;
                color: white;
            }
            """


class DraggerSlider(QDoubleSpinBox, object):
    """
    Slider that holds Houdini style draggers to drag values when mid click over them.
    Middle click to display draggers to change value by adding different delta values
    """

    valueIncremented = Signal(object)

    def __init__(self, label_text='', slider_type='float', buttons=False, decimals=3, dragger_steps=None,
                 apply_style=True, main_color=None, *args, **kwargs):
        super(DraggerSlider, self).__init__(*args, **kwargs)

        self._label_text = label_text
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()
        self._dragger_steps = dragger_steps or FLOAT_SLIDER_DRAG_STEPS
        self._is_float = slider_type == 'float'
        self._draggers = None

        self.setFocusPolicy(Qt.StrongFocus)
        if not self._is_float:
            self.setDecimals(0)
            self.setRange(qtutils.FLOAT_RANGE_MIN, qtutils.FLOAT_RANGE_MAX)
        else:
            self.setDecimals(decimals)
            self.setRange(qtutils.INT_RANGE_MIN, qtutils.INT_RANGE_MAX)
        if not buttons:
            self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        if apply_style:
            self._label_font = QFont('Serif', 10, QFont.Bold)
            self.setStyleSheet(self._get_style_sheet())
        else:
            self._label_font = self.lineEdit().font()

        self.lineEdit().installEventFilter(self)
        self.installEventFilter(self)

    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super(DraggerSlider, self).wheelEvent(event)

    def update(self):
        self.setStyleSheet(self._get_style_sheet())

    def paintEvent(self, event):
        super(DraggerSlider, self).paintEvent(event)

        p = QPainter()
        p.begin(self)
        p.setPen(color.DARK_GRAY)
        p.setFont(self._label_font)
        p.drawText(self.rect(), Qt.AlignCenter, self._label_text)
        p.end()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                if not self._draggers:
                    self._draggers = SliderDraggers(self, self._is_float, dragger_steps=self._dragger_steps)
                    self._draggers.increment.connect(self._on_value_incremented)
                self._draggers.show()
                if self._is_float:
                    self._draggers.move(
                        self.mapToGlobal(QPoint(event.pos().x() - 1, event.pos().y() - self._draggers.height() / 2)))
                else:
                    self._draggers.move(
                        self.mapToGlobal(QPoint(event.pos().x() - 1, event.pos().y() - self._draggers.height() + 15)))

        return False

    def _get_style_sheet(self):
        return """
        QWidget{
            border: 1.25 solid black;
        }
        QSlider::groove:horizontal,
            QSlider::sub-page:horizontal {
            background: %s;
        }
        QSlider::add-page:horizontal,
            QSlider::sub-page:horizontal:disabled {
            background: rgb(32, 32, 32);
        }
        QSlider::add-page:horizontal:disabled {
            background: grey;
        }
        QSlider::handle:horizontal {
            width: 1px;
         }
        """ % "rgba%s" % str(self._main_color)

    def _on_value_incremented(self, step):
        self.valueIncremented.emit(step)
        self.setValue(self.value() + step)


@mixin.theme_mixin
class HoudiniDoubleSlider(QWidget, object):
    """
    Slider that encapsulates a DoubleSlider and Houdini draggers linked together
    """

    valueChanged = Signal(object)

    def __init__(self, parent, slider_type='float', style=0, name=None, slider_range=None, default_value=0.0,
                 dragger_steps=None, main_color=None, *args):
        if slider_range is None:
            slider_range = (-100.0, 100.0)
        if dragger_steps is None:
            dragger_steps = FLOAT_SLIDER_DRAG_STEPS
        super(HoudiniDoubleSlider, self).__init__(parent=parent, *args)

        h = 20
        self._parent = parent
        self._type = slider_type
        self._value = 0.0
        self._label = None
        self._style_type = style

        theme = self.theme()
        if theme:
            theme_color = theme.accent_color
            if core_color.string_is_hex(theme_color):
                theme_color = core_color.hex_to_rgb(theme_color)
                main_color = QColor(*theme_color).getRgb()

        self._main_color = main_color or QColor(215, 128, 26).getRgb()

        self.setMaximumHeight(h)
        self.setMinimumHeight(h)

        self._main_layout = QHBoxLayout()
        self._main_layout.setContentsMargins(10, 0, 0, 0)
        self.setLayout(self._main_layout)

        self._input = DraggerSlider(slider_type=slider_type)
        self._input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._input.setRange(slider_range[0], slider_range[1])
        self._input.setContentsMargins(0, 0, 0, 0)
        self._input.setMinimumWidth(50)
        self._input.setMaximumWidth(50)
        self._input.setMinimumHeight(h)
        self._input.setMaximumHeight(h)
        self._input.valueIncremented.connect(self._on_increment_value)

        if self._type == 'float':
            self._slider = DoubleSlider(parent=self, default_value=default_value, slider_range=slider_range,
                                        dragger_steps=dragger_steps)
        else:
            self._slider = Slider(parent=self, slider_range=slider_range)
            self._slider.valueIncremented.connect(self._on_increment_value)
        self._slider.setContentsMargins(0, 0, 0, 0)
        self._slider.setMinimumHeight(h)
        self._slider.setMaximumHeight(h)

        if name:
            self._label = QLabel(name + '  ')
            self._main_layout.addWidget(self._label)
        self._main_layout.addWidget(self._input)
        self._main_layout.addWidget(self._slider)

        style_sheet = self._get_style_sheet(self._style_type)
        if self._style_type == 0:
            self._main_layout.setSpacing(0)
        self._slider.setStyleSheet(style_sheet)

        self._slider.valueChanged.connect(self._on_slider_value_changed)
        self._input.valueChanged.connect(self._on_houdini_slider_value_changed)

    def update(self):
        style_sheet = self._get_style_sheet(self._style_type)
        if self._style_type == 0:
            self._main_layout.setSpacing(0)
        self._slider.setStyleSheet(style_sheet)

    @property
    def minimum(self):
        return self._input.minimum()

    @property
    def maximum(self):
        return self._input.maximum()

    @property
    def _value_range(self):
        return self.maximum - self.minimum

    def value(self):
        self._value = self._input.value()
        if self._type == 'int':
            self._value = int(self._value)

        return self._value

    def set_value(self, value):
        self._input.setValue(value)
        self._value = self._input.value()
        self.valueChanged.emit(self.value())
        self._on_houdini_slider_value_changed(0)

    def set_decimals(self, decimals):
        self._input.setDecimals(decimals)

    def set_single_step(self, step):
        self._input.setSingleStep(step)

    def hide_label(self):
        if self._label:
            self._label.hide()

    def show_label(self):
        if self._label:
            self._label.show()

    def hide_slider(self):
        self._slider.hide()

    def show_slider(self):
        self._slider.show()

    def set_range(self, minimum_value, maximum_value):
        self._input.setRange(minimum_value, maximum_value)

    def _on_increment_value(self, step):
        if step == 0.0:
            return
        old = self._input.value()
        new = old + step
        self._input.setValue(new)
        self.valueChanged.emit(new)

    def _on_slider_value_changed(self, value):
        out_value = mathlib.map_range_unclamped(
            value, self._slider.minimum(), self._slider.maximum(), self._input.minimum(), self._input.maximum())
        self._input.blockSignals(True)
        self._input.setValue(out_value)
        self._input.blockSignals(False)
        self.valueChanged.emit(out_value)

    def _on_houdini_slider_value_changed(self, value):
        in_value = mathlib.map_range_unclamped(
            self._input.value(), self._input.minimum(), self._input.maximum(),
            self._slider.minimum(), self._slider.maximum())
        self._slider.blockSignals(True)
        self._slider.setValue(int(in_value))
        self._slider.blockSignals(False)
        self.valueChanged.emit(value)

    def _get_style_sheet(self, style_type):
        if style_type == 0:
            return """
            QWidget{
                border: 1.25 solid black;
            }
            QSlider::groove:horizontal,
                QSlider::sub-page:horizontal {
                background: %s;
            }
            QSlider::add-page:horizontal,
                QSlider::sub-page:horizontal:disabled {
                background: rgb(32, 32, 32);
            }
            QSlider::add-page:horizontal:disabled {
                background: grey;
            }
            QSlider::handle:horizontal {
                width: 1px;
             }
            """ % "rgba%s" % str(self._main_color)
        else:
            return """
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 3px;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: %s;
                border: 0px solid #777;
                height: 3px;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #fff;
                border: 1px solid #777;
                height: 3px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eee, stop:1 #ccc);
                border: 1px solid #777;
                width: 4px;
                margin-top: -8px;
                margin-bottom: -8px;
                border-radius: 2px;
                height : 10px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fff, stop:1 #ddd);
                border: 1px solid #444;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal:disabled {
                background: #bbb;
                border-color: #999;
            }
            QSlider::add-page:horizontal:disabled {
                background: #eee;
                border-color: #999;
            }
            QSlider::handle:horizontal:disabled {
                background: #eee;
                border: 1px solid #aaa;
                border-radius: 2px;
                height : 10;
            }
            """ % "rgba%s" % str(self._main_color)


class GradientSlider(DoubleSlider, object):
    """
    Custom slider to select a color by non editable gradient
    """

    def __init__(self, parent, color1=None, color2=None, slider_range=None, dragger_steps=None, main_color=None, *args):
        if color1 is None:
            color1 = [0, 0, 0]
        if color2 is None:
            color2 = [255, 255, 255]
        if slider_range is None:
            slider_range = (0.0, 255.0)
        if dragger_steps is None:
            dragger_steps = [5.0, 1.0, 0.25]
        super(GradientSlider, self).__init__(
            parent=parent, slider_range=slider_range, dragger_steps=dragger_steps, *args)

        self._parent = parent
        self._color1 = QColor(color1[0], color1[1], color1[2])
        self._color2 = QColor(color2[0], color2[1], color2[2])
        self._main_color = main_color if main_color else QColor(215, 128, 26).getRgb()

        self.setStyleSheet(self._get_style_sheet())

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        self._draw_widget(painter)
        painter.end()
        super(GradientSlider, self).paintEvent(event)

    def get_color(self):
        """
        Computes and returns current color
        :return: list(float, float, float)
        """

        r1, g1, b1 = self._color1.getRgb()
        r2, g2, b2 = self._color2.getRgb()
        f_r = (r2 - r1) * self.mapped_value() + r1
        f_g = (g2 - g1) * self.mapped_value() + g1
        f_b = (b2 - b1) * self.mapped_value() + b1

        return [f_r, f_g, f_b]

    def _draw_widget(self, painter):
        width = self.width()
        height = self.height()

        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, self._color1)
        gradient.setColorAt(1, self._color2)
        painter.setBrush(QBrush(gradient))

        painter.drawRect(0, 0, width, height)

    def _get_style_sheet(self):
        return """
        QSlider,QSlider:disabled,QSlider:focus{
                                  background: qcolor(0,0,0,0);   }

         QSlider::groove:horizontal {
            border: 1px solid #999999;
            background: qcolor(0,0,0,0);
         }
        QSlider::handle:horizontal {
            background:  rgba(255, 255, 255, 150);
            width: 10px;
            border-radius: 4px;
            border: 1.5px solid black;
         }
         QSlider::handle:horizontal:hover {
            border: 2.25px solid %s;
         }
        """ % "rgba%s" % str(self._main_color)


class ColorSlider(QWidget, object):
    """
    Custom slider to choose a color by its components
    """

    valueChanged = Signal(list)

    def __init__(self, parent=None, start_color=None, slider_type='float', alpha=False, height=50, *args):
        super(ColorSlider, self).__init__(parent=parent, *args)

        self._parent = parent
        self._type = slider_type
        self._alpha = alpha
        self._default_color = start_color
        self._style_str = "QPushButton{ background-color: rgba(%f,%f,%f,%f);border-color: black;" \
                          "border-radius: 2px;border-style: outset;border-width: 1px;}" \
                          "\nQPushButton:pressed{ border-style: inset;border-color: beige}"

        main_layout = QHBoxLayout()
        main_layout.setSpacing(5)
        self.setLayout(main_layout)
        self.setMaximumHeight(height)
        self._menu = QMenu()
        self._action_reset = self._menu.addAction('Reset Value')

        self._red_dragger = DraggerSlider(slider_type=self._type)
        self._green_dragger = DraggerSlider(slider_type=self._type)
        self._blue_dragger = DraggerSlider(slider_type=self._type)
        self._alpha_dragger = DraggerSlider(slider_type=self._type)
        for dragger in [self._red_dragger, self._green_dragger, self._blue_dragger, self._alpha_dragger]:
            dragger.setMinimum(0)
            if slider_type == 'int':
                dragger.setMaximum(255)
            else:
                dragger.setMaximum(1.0)

        self._red_slider = GradientSlider(parent=self, color2=[255, 0, 0])
        self._green_slider = GradientSlider(parent=self, color2=[0, 255, 0])
        self._blue_slider = GradientSlider(parent=self, color2=[0, 0, 255])
        self._alpha_slider = GradientSlider(parent=self, color2=[255, 255, 255])

        self._red_dragger.valueChanged.connect(lambda value: self._red_slider.set_mapped_value(float(value)))
        self._red_slider.doubleValueChanged.connect(lambda value: self._red_dragger.setValue(value))
        self._green_dragger.valueChanged.connect(lambda value: self._green_slider.set_mapped_value(float(value)))
        self._green_slider.doubleValueChanged.connect(lambda value: self._green_dragger.setValue(value))
        self._blue_dragger.valueChanged.connect(lambda value: self._blue_slider.set_mapped_value(float(value)))
        self._blue_slider.doubleValueChanged.connect(lambda value: self._blue_dragger.setValue(value))
        self._alpha_dragger.valueChanged.connect(lambda value: self._alpha_slider.set_mapped_value(float(value)))
        self._alpha_slider.doubleValueChanged.connect(lambda value: self._alpha_dragger.setValue(value))

        red_layout = QHBoxLayout()
        green_layout = QHBoxLayout()
        blue_layout = QHBoxLayout()
        alpha_layout = QHBoxLayout()
        red_layout.addWidget(self._red_dragger)
        red_layout.addWidget(self._red_slider)
        green_layout.addWidget(self._green_dragger)
        green_layout.addWidget(self._green_slider)
        blue_layout.addWidget(self._blue_dragger)
        blue_layout.addWidget(self._blue_slider)
        alpha_layout.addWidget(self._alpha_dragger)
        alpha_layout.addWidget(self._alpha_slider)
        self._sliders_layout = QVBoxLayout()
        self._sliders_layout.setSpacing(0)
        layouts_list = [red_layout, green_layout, blue_layout]
        if self._alpha:
            layouts_list.append(alpha_layout)
        else:
            self._alpha_slider.hide()

        self._alpha_slider.set_mapped_value(255)

        self._color_btn = QPushButton()
        self._color_btn.setMaximumWidth(height)
        self._color_btn.setMinimumWidth(height)
        self._color_btn.setMaximumHeight(height - 12)
        self._color_btn.setMinimumHeight(height - 12)
        self._color_btn.setStyleSheet(
            self._style_str % (
                self._red_slider.mapped_value(), self._green_slider.mapped_value(),
                self._blue_slider.mapped_value(), self._alpha_slider.mapped_value()))

        for widget in [self._red_slider, self._green_slider, self._blue_slider, self._alpha_slider,
                       self._red_dragger, self._green_dragger, self._blue_dragger, self._alpha_dragger]:
            widget.setMaximumHeight(height / len(layouts_list) + 1)
            widget.setMinimumHeight(height / len(layouts_list) + 1)

        for slider in [self._red_slider, self._green_slider, self._blue_slider, self._alpha_slider]:
            slider.doubleValueChanged.connect(self._on_color_changed)

        for layout in layouts_list:
            self._sliders_layout.addLayout(layout)

        main_layout.addWidget(self._color_btn)
        main_layout.addLayout(self._sliders_layout)

        if isinstance(start_color, list) and len(start_color) >= 3:
            self.set_color(start_color)

        self._color_btn.clicked.connect(self._on_show_color_dialog)
        self._action_reset.triggered.connect(self._on_reset_value)

    def contextMenuEvent(self, event):
        self._menu.exec_(event.globalPos())

    def set_color(self, new_color):
        self._red_slider.set_mapped_value(new_color[0])
        self._green_slider.set_mapped_value(new_color[1])
        self._green_slider.set_mapped_value(new_color[2])
        if len(new_color) > 3:
            self._alpha_slider.set_mapped_value(new_color[3])

    def _on_color_changed(self):
        self._color_btn.setStyleSheet(
            self._style_str % (
                self._red_slider.mapped_value(), self._green_slider.mapped_value(),
                self._blue_slider.mapped_value(), self._alpha_slider.mapped_value()))
        value_list = [
            self._red_slider.mapped_value(), self._green_slider.mapped_value(), self._blue_slider.mapped_value()]
        if self._alpha:
            value_list.append(self._alpha_slider.mapped_value())
        if self._type == 'int':
            value_list = [mathlib.clamp(int(i), 0, 255) for i in value_list]
        self.valueChanged.emit(value_list)

    def _on_show_color_dialog(self):
        if self._alpha:
            new_color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
        else:
            new_color = QColorDialog.getColor()
        if new_color.isValid():
            self._red_slider.set_mapped_value(
                mathlib.map_range_unclamped(
                    new_color.redF(), 0.0, 1.0, self._red_slider.slider_range[0], self._red_slider.slider_range[1]))
            self._green_slider.set_mapped_value(
                mathlib.map_range_unclamped(
                    new_color.greenF(), 0.0, 1.0, self._green_slider.slider_range[0],
                    self._green_slider.slider_range[1]))
            self._blue_slider.set_mapped_value(
                mathlib.map_range_unclamped(
                    new_color.blueF(), 0.0, 1.0, self._blue_slider.slider_range[0], self._blue_slider.slider_range[1]))
            self._alpha_slider.set_mapped_value(
                mathlib.map_range_unclamped(
                    new_color.alphaF(), 0.0, 1.0, self._alpha_slider.slider_range[0],
                    self._alpha_slider.slider_range[1]))

    def _on_reset_value(self):
        if self._default_color:
            self.set_color(self._default_color)
