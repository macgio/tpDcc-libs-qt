#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt stack widgets
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.qt.core import consts, qtutils, base, dpi, mixin
from tpDcc.libs.qt.widgets import layouts, buttons, lineedit


class SlidingStackedWidget(QStackedWidget, object):
    """
    QStackedWidget width sliding functionality
    """

    animFinished = Signal(int)

    def __init__(self, parent=None, **kwargs):
        super(SlidingStackedWidget, self).__init__(parent)

        # This variable holds the current widget without taking into account if the animation has finished or not
        self._speed = kwargs.pop('speed', 500)
        self._current_widget = None
        self._animation_type = kwargs.pop('animation_type', QEasingCurve.OutCubic)
        self._wrap = kwargs.pop('wrap', True)
        self._vertical = kwargs.pop('vertical', False)
        self._active_state = False
        self._blocked_page_list = list()
        self._now = 0
        self._next = 1

    @property
    def current_widget(self):
        return self._current_widget

    def set_speed(self, speed):
        """
        Sets the animation speed of the sliding
        :param speed: int
        """

        self._speed = speed

    def set_animation(self, animation_type):
        """
        Set the curve animation type of the sliding
        :param animation_type: QEasingCurve
        """

        self._animation_type = animation_type

    def set_vertical_mode(self, vertical=True):
        """
        Sets whether the sliding animation is done vertically or horizontally
        :param vertical: bool
        """

        self._vertical = vertical

    def set_wrap(self, wrap):
        """
        Sets whether the page index is restarted when we arrive the last one or not
        :param wrap: bool
        """

        self._wrap = wrap

    def slide_in_next(self):
        """
        Slides into the next widget
        """

        now = self.currentIndex()
        if self._wrap or now < self.count() - 1:
            self.slide_in_index(now + 1)

    def slide_in_prev(self):
        """
        Slides into the previous widget
        """

        now = self.currentIndex()
        if self._wrap or now > 0:
            self.slide_in_index(now - 1)

    def slide_in_index(self, next, force=False):
        """
        Slides to the given widget index
        :param next: int, index of the widget to slide
        """

        now = self.currentIndex()
        if (self._active_state or next == now) and not force:
            return

        self._active_state = True
        width, height = self.frameRect().width(), self.frameRect().height()
        next %= self.count()
        if next > now:
            if self._vertical:
                offset_x, offset_y = 0, height
            else:
                offset_x, offset_y = width, 0
        else:
            if self._vertical:
                offset_x, offset_y = 0, -height
            else:
                offset_x, offset_y = -width, 0
        self.widget(next).setGeometry(0, 0, width, height)
        pnow, pnext = self.widget(now).pos(), self.widget(next).pos()
        self._point_now = pnow

        self.widget(next).move(pnext.x() + offset_x, pnext.y() + offset_y)
        self.widget(next).show()
        self.widget(next).raise_()
        self._current_widget = self.widget(next)

        anim_now = QPropertyAnimation(self.widget(now), 'pos')
        anim_now.setDuration(self._speed)
        anim_now.setStartValue(pnow)
        anim_now.setEndValue(QPoint(pnow.x() - offset_x, pnow.y() - offset_y))
        anim_now.setEasingCurve(self._animation_type)

        anim_next = QPropertyAnimation(self.widget(next), 'pos')
        anim_next.setDuration(self._speed)
        anim_next.setStartValue(QPoint(offset_x + pnext.x(), offset_y + pnext.y()))
        anim_next.setEndValue(pnext)
        anim_next.setEasingCurve(self._animation_type)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(anim_now)
        self._anim_group.addAnimation(anim_next)
        self._anim_group.finished.connect(self._animation_done_slot)
        self._anim_group.start()

        self._next = next
        self._now = now

    def _animation_done_slot(self):
        self.setCurrentIndex(self._next)
        self.widget(self._now).hide()
        self.widget(self._now).move(self._point_now)
        try:
            self.widget(self._now).update()
        except Exception:
            pass
        self._active_state = False
        self.animFinished.emit(self._next)


@mixin.stacked_opacity_animation_mixin
class SlidingOpacityStackedWidget(QStackedWidget, object):
    """
    Custom stack widget that activates opacity animation when current stack index changes
    """

    def __init__(self, parent=None):
        super(SlidingOpacityStackedWidget, self).__init__(parent)


class StackItem(QFrame, object):

    minimized = Signal()
    maximized = Signal()
    toggleExpandRequested = Signal(bool)
    shiftUpPressed = Signal()
    shiftDownPressed = Signal()
    deletePressed = Signal()
    updateRequested = Signal()

    def __init__(self, title, parent, collapsed=False, collapsable=True, icon=None, start_hidden=False,
                 shift_arrows_enabled=True, delete_button_enabled=True, title_editable=True,
                 icon_size=12, title_frame=None, show_item_icon=True):
        super(StackItem, self).__init__(parent)

        self._stack_widget = parent
        self._icon_size = icon_size
        self._title = title
        self._title_editable = title_editable
        self._icon = icon
        self._shift_arrows_enabled = shift_arrows_enabled
        self._delete_button_enabled = delete_button_enabled
        self._color = consts.DARK_BG_COLOR
        self._contents_margins = (0, 0, 0, 0)
        self._contents_spacing = 0
        self._collapsable = collapsable
        self._collapsed = collapsed
        self._title_frame = title_frame
        self._show_item_icon = show_item_icon

        if start_hidden:
            self.hide()

        self.ui()
        self.setup_signals()

        if not collapsable:
            self._collapsed = False
            self.expand()

        if self._collapsed:
            self.collapse()
        else:
            self.expand()

    @property
    def contents_layout(self):
        return self._contents_layout

    @property
    def collapsed(self):
        return self._collapsed

    def ui(self):
        # theme = tpDcc.ToolsMgr().get_tool_theme('tpDcc-tools-hub')
        # border_width = qtutils.dpi_scale_divide(theme.STACK_BORDER_WIDTH)
        border_width = qtutils.dpi_scale_divide(1)
        self.main_layout = layouts.VerticalLayout(
            margins=(border_width, border_width, border_width, border_width), spacing=0)
        self.setLayout(self.main_layout)

        if not self._title_frame:
            self._title_frame = StackTitleFrame(
                title=self._title, icon=self._icon, title_editable=self._title_editable,
                item_icon_size=self._icon_size, collapsed=self._collapsed,
                shift_arrows_enabled=self._shift_arrows_enabled, delete_button_enabled=self._delete_button_enabled)
        if not self._show_item_icon:
            self._title_frame.item_icon_button.hide()

        self._widget_hider = StackHiderWidget(parent=self)
        self._contents_layout = layouts.VerticalLayout(spacing=0)
        self._contents_layout.setContentsMargins(*self._contents_margins)
        self._contents_layout.setSpacing(self._contents_spacing)
        self._widget_hider.setLayout(self._contents_layout)
        self._widget_hider.setContentsMargins(0, 0, 0, 0)
        self._widget_hider.setHidden(self._collapsed)
        self._widget_hider.setObjectName('stackbody')

        self.main_layout.addWidget(self._title_frame)
        self.main_layout.addWidget(self._widget_hider)

    def setup_signals(self):
        self._title_frame.expand_toggle_button.leftClicked.connect(self._on_toggle_contents)
        self._title_frame.minimized.connect(self.minimized.emit)
        self._title_frame.maximized.connect(self.maximized.emit)
        self._title_frame.toggleExpandRequested.connect(self.toggleExpandRequested.emit)
        self._title_frame.shiftUpPressed.connect(self.shiftUpPressed.emit)
        self._title_frame.shiftDownPressed.connect(self.shiftDownPressed.emit)
        self._title_frame.deletePressed.connect(self.deletePressed.emit)
        self._title_frame.updateRequested.connect(self.updateRequested.emit)

    def title_text_widget(self):
        """
        Returns title text widget
        :return: QLineEdit
        """

        return self._title_frame.line_edit

    def get_title(self):
        """
        Returns title text
        :return: str
        """

        return self._title_frame.line_edit.text()

    def set_title(self, text):
        """
        Function that sets title text
        :param text: str
        """

        self._title_frame.line_edit.setText(text)

    def add_widget(self, widget):
        """
        Adds a new widget to the contents layout
        :param widget: QWidget
        """

        self._contents_layout.addWidget(widget)

    def add_layout(self, layout):
        """
        Adds a new layout to the contents layout
        :param layout: QLayout
        """

        self._contents_layout.addLayout(layout)

    def expand(self, emit=True):
        """
        Function that expands the contents and show all the widget data
        :param emit: bool
        """

        self._on_expand(emit)

    def collapse(self, emit=True):
        """
        Function that collapses and hides the contents
        :param emit: bool
        """

        self._on_collapse(emit)

    def show_expand_indicator(self, flag):
        """
        Sets whether expand indicator is visible or not
        :param flag: bool
        """

        self._title_frame.expand_toggle_button.setVisible(flag)

    def set_title_text_mouse_transparent(self, flag):
        """
        Sets whether or not title text mouse is transparent
        :param flag: bool
        """

        self._title_frame.line_edit.setAttribute(Qt.WA_TransparentForMouseEvents, flag)

    def set_item_icon_color(self, color):
        """
        Sets the color of the item in title
        :param color: tuple(int, int, int), RGB color in 0-255 range
        """

        self._title_frame.set_item_icon_color(color)

    def set_item_icon(self, icon):
        """
        Sets the icon of the item in title
        :param icon: QIcon
        """

        self.title_frame.set_item_icon(icon)

    def shift_up(self):
        """
        Emits item shift up signal
        """

        self.shiftUpPressed.emit()

    def shift_down(self):
        """
        Emits shijft down signal
        """

        self.shiftDownPressed.emit()

    def set_arrows_visible(self, flag):
        """
        Sets whether shift arrows are visible or not.
        This arrows allow the item to be shifted upwards or downwards the stack
        :param flag: bool
        """

        if flag:
            self._title_frame.shift_down_button.show()
            self._title_frame.shift_up_button.show()
        else:
            self._title_frame.shift_down_button.hide()
            self._title_frame.shift_up_button.hide()

    def update_size(self):
        """
        Updates the size of the widget, to fit to new size depending on its contents
        """

        self.updateRequested.emit()

    def _on_expand(self, emit=True):
        """
        Internal function that expands the contents and show all the widget data
        :param emit: bool
        """

        self._widget_hider.setHidden(False)
        self._title_frame.expand()
        if emit:
            self.maximized.emit()
        self._collapsed = False

    def _on_collapse(self, emit=True):
        """
        Internal function that collapses and hides the contents
        :param emit: bool
        """

        self._widget_hider.setHidden(True)
        self._title_frame.collapse()
        if emit:
            self.minimized.emit()
        self._collapsed = True

    def _on_toggle_contents(self, emit=True):
        """
        Internal callback function that shows and hides the hidder widget and shows/hides contents
        :param emit: bool
        """

        if not self._collapsable:
            return

        self.toggleExpandRequested.emit(not self._collapsed)
        if self._collapsed:
            self.expand(emit)
            self.update_size()
            return not self._collapsed

        self.collapse(emit)
        self.update_size()
        return self._collapsed


class StackHiderWidget(base.BaseFrame, object):
    def __init__(self, parent=None):
        super(StackHiderWidget, self).__init__(parent)


class StackTitleFrame(QFrame, dpi.DPIScaling):

    minimized = Signal()
    maximized = Signal()
    toggleExpandRequested = Signal(bool)
    shiftUpPressed = Signal()
    shiftDownPressed = Signal()
    deletePressed = Signal()
    updateRequested = Signal()

    def __init__(self, title='', title_editable=False, icon=None, item_icon_size=16, collapsed=True,
                 shift_arrows_enabled=True, delete_button_enabled=True, parent=None):
        super(StackTitleFrame, self).__init__(parent)

        self._title = title
        self._item_icon = icon or 'tpdcc'
        self._title_editable = title_editable
        self._shift_arrows_enabled = shift_arrows_enabled
        self._delete_button_enabled = delete_button_enabled
        self._spaces_to_underscore = False
        self._collapsed = collapsed
        self._item_icon_size = item_icon_size

        self._collapsed_icon = tpDcc.ResourcesMgr().icon('sort_closed')
        self._expand_icon = tpDcc.ResourcesMgr().icon('sort_down')

        self.setObjectName('title')

        self.ui()
        self.setup_signals()

        self.setFixedHeight(self.sizeHint().height())
        self.setMinimumSize(self.sizeHint().width(), self.sizeHint().height() + 1)

    @property
    def horizontal_layout(self):
        return self._horizontal_layout

    @property
    def item_icon(self):
        return self._item_icon

    @property
    def item_icon_button(self):
        return self._item_icon_btn

    @property
    def expand_toggle_button(self):
        return self._expand_toggle_btn

    @property
    def shift_down_button(self):
        return self._shift_down_btn

    @property
    def shift_up_button(self):
        return self._shift_up_btn

    @property
    def delete_button(self):
        return self._delete_btn

    @property
    def line_edit(self):
        return self._line_edit

    def mouseDoubleClickEvent(self, event):
        if self._title_editable:
            self._line_edit.editEvent(event)

    def ui(self):

        item_icon = tpDcc.ResourcesMgr().icon(self._item_icon)
        if item_icon.isNull():
            item_icon = tpDcc.ResourcesMgr().icon('tpdcc')
        delete_icon = tpDcc.ResourcesMgr().icon('delete')
        shift_up_icon = tpDcc.ResourcesMgr().icon('arrow_up')
        shift_down_icon = tpDcc.ResourcesMgr().icon('arrow_down')

        self.setContentsMargins(*qtutils.margins_dpi_scale(0, 0, 0, 0))
        self._extras_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0), spacing=0)
        self._horizontal_layout = layouts.HorizontalLayout(spacing=0)
        self.setLayout(self._horizontal_layout)

        self._line_edit = lineedit.ClickLineEdit(self._title)
        self._line_edit.setObjectName('lineEdit')
        self._line_edit.setFocusPolicy(Qt.NoFocus)
        self._line_edit.setVisible(False)
        self._line_edit.setAttribute(Qt.WA_TransparentForMouseEvents)
        if not self._title_editable:
            self._line_edit.setReadOnly(True)

        self._expand_toggle_btn = buttons.BaseMenuButton()
        self._item_icon_btn = buttons.BaseMenuButton()
        self._shift_down_btn = buttons.BaseMenuButton()
        self._shift_up_btn = buttons.BaseMenuButton()
        self._delete_btn = buttons.BaseMenuButton()

        if not self._shift_arrows_enabled:
            self._shift_down_btn.hide()
            self._shift_up_btn.hide()
        if not self._delete_button_enabled:
            self._delete_btn.hide()

        self._item_icon_btn.set_icon(icon=item_icon, size=self._item_icon_size)
        self._item_icon_btn.setAttribute(Qt.WA_TransparentForMouseEvents)

        icon_size = 12
        highlight_offset = 40
        self._delete_btn.set_icon(delete_icon, colors=None, size=icon_size, color_offset=highlight_offset)
        self._shift_up_btn.set_icon(shift_up_icon, colors=None, size=icon_size, color_offset=highlight_offset)
        self._shift_down_btn.set_icon(shift_down_icon, colors=None, size=icon_size, color_offset=highlight_offset)
        self._expand_toggle_btn.set_icon(self._expand_icon, colors=(192, 192, 192), size=icon_size)

        self._horizontal_layout.addWidget(self._item_icon_btn)
        self._horizontal_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self._horizontal_layout.addWidget(self._line_edit)
        self._horizontal_layout.addLayout(self._extras_layout)
        self._horizontal_layout.addWidget(self._shift_up_btn)
        self._horizontal_layout.addWidget(self._shift_down_btn)
        self._horizontal_layout.addWidget(self._expand_toggle_btn)
        self._horizontal_layout.addWidget(self._delete_btn)
        self._horizontal_layout.setStretchFactor(self._line_edit, 4)

    def setup_signals(self):
        self._shift_up_btn.leftClicked.connect(self._on_shift_up)
        self._shift_down_btn.leftClicked.connect(self._on_shift_down)
        self._delete_btn.leftClicked.connect(self.deletePressed.emit)
        self._line_edit.textChanged.connect(self._on_title_validate)
        self._line_edit.selectionChanged.connect(self._on_select_check)

    def collapse(self):
        self._expand_toggle_btn.set_icon(self._collapsed_icon, colors=(192, 192, 192), size=12)

    def expand(self):
        self._expand_toggle_btn.set_icon(self._expand_icon, colors=(192, 192, 192), size=12)

    def set_item_icon_color(self, color):
        self._item_icon_btn.set_icon_color(color)

    def set_item_icon(self, icon):
        self._item_icon_btn.set_icon(icon)

    def _on_shift_up(self):
        self.shiftUpPressed.emit()

    def _on_shift_down(self):
        self.shiftDownPressed.emit()

    def _on_title_validate(self):
        """
        Internal callback function that is called when line edit text changes
        Removes invalid characters and replaces spaces with underscores
        """

        if self._spaces_to_underscore:
            line_edit = self._line_edit
            text = self._line_edit.text()
            pos = line_edit.cursorPosition()
            text = text.replace(' ', '_')
            line_edit.blockSignals(True)
            try:
                line_edit.setText(text)
            finally:
                line_edit.blockSignals(False)
            line_edit.setCursorPosition(pos)

    def _on_select_check(self):
        """
        Internal callback function that is called when user deselects line edit
        Stops any selection from happening if title is not editable
        """

        if not self._title_editable:
            self._line_edit.deselect()
