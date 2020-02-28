#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle tools
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.widgets import stack, buttons


class ToolsetWidget(stack.StackItem, object):

    ID = 'toolsetID'
    CONFIG = None
    EXTENSION = 'toolset'

    def __init__(self, tree_widget=None, icon_color=(255, 255, 255), widget_item=None, parent=None):

        self._block_save = False
        self._show_warnings = True
        self._icon = self.CONFIG.get('icon')
        self._icon_color = icon_color
        self._tree_widget = tree_widget
        self._toolset_widget_item = widget_item
        self._stacked_widget = None
        self._display_mode_button = None
        self._help_button = None
        self._widgets = list()
        title = self.CONFIG.get('label', 'Not defined')

        super(ToolsetWidget, self).__init__(
            title=title, collapsed=True, icon=self._icon, shift_arrows_enabled=False,
            title_editable=False, parent=parent or tree_widget)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def stacked_widget(self):
        return self._stacked_widget

    # =================================================================================================================
    # TO OVERRIDE
    # =================================================================================================================

    def pre_content_setup(self):
        """
        Function that is called before toolset contents are created
        Override in specific toolset widgets
        """

        pass

    def contents(self):
        """
        Returns toolset widget contentS
        Override in specific toolset widgets
        :return:
        """

        pass

    def post_content_setup(self):
        """
        Function that is called after toolset contents are created
        Override in specific toolset widgets
        """

        pass

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def ui(self):
        super(ToolsetWidget, self).ui()

        # self.setContentsMargins(0, 0, 0, 0)
        # self._contents_layout.setContentsMargins(0, 0, 0, 0)
        # self._contents_layout.setSpacing(0)

        # self._stacked_widget = QStackedWidget(self._widget_hider)
        self._stacked_widget = QStackedWidget()
        self._stacked_widget.setContentsMargins(0, 0, 0, 0)
        self._stacked_widget.setLineWidth(0)
        # self._contents_layout.addWidget(self._stacked_widget)
        self.main_layout.addWidget(self._stacked_widget)

        # self.show_expand_indicator(False)
        # self.set_title_text_mouse_transparent(True)
        #
        # self._display_mode_button = DisplayModeButton(color=self._icon_color, size=16, parent=self)
        # self._display_mode_button.setIconSize(QSize(20, 20))
        # self._help_button = buttons.BaseMenuButton(parent=self)
        # self._help_button.set_icon(tpDcc.ResourcesMgr().icon('help'))
        # self._help_button.setIconSize(QSize(15, 15))

    #     # We call if after setting all buttons
    #     self.set_icon_color(self._icon_color)
    #
    #     self.visual_update(collapse=True)
    #
    #     display_button_pos = 7
    #     self._title_frame.horizontal_layout.insertWidget(display_button_pos - 1, self._help_button)
    #     self._title_frame.horizontal_layout.insertWidget(display_button_pos, self._display_mode_button)
    #     self._title_frame.horizontal_layout.setSpacing(0)
    #     self._title_frame.horizontal_layout.setContentsMargins(0, 0, 0, 0)
    #     self._title_frame.delete_button.setIconSize(QSize(12, 12))
    #     self._title_frame.item_icon.setIconSize(QSize(20, 20))
    #
    #     font = QFont()
    #     font.setBold(True)
    #     self.setFont(font)
    #
    # def setup_signals(self):
    #     super(ToolsetWidget, self).setup_signals()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    # def widgets(self):
    #     """
    #     Returns all display widgets
    #     :return: list
    #     """
    #
    #     return self._widgets
    #
    # def display_index(self):
    #     """
    #     Current index of the stacked widget
    #     :return: int
    #     """
    #
    #     return self._stacked_widget.currentIndex()
    #
    # def current_widget(self):
    #     """
    #     Returns current active widget
    #     :return: QWidget
    #     """
    #
    #     return self.widgets()[self.display_index()]
    #
    # def widget_at(self, index):
    #     """
    #     Returns stacked widget at given index
    #     :param index: int
    #     :return: QWidget
    #     """
    #
    #     return self._stacked_widget.widget(index)
    #
    # def count(self):
    #     """
    #     Returns the total amount of widgets added to the stack
    #     :return: int
    #     """
    #
    #     return self._stacked_widget.count()

    def add_stacked_widget(self, widget):
        """
        Adds a new widget to the stack
        :param widget: QWidget
        """

        if not widget:
            raise ValueError(
                'Toolset "{}" contents() must return a list of widgets! None found.'.format(
                    str(self.__class__.__name__)))

        self._widgets.append(widget)
        # widget.setParent(self._widget_hider)
        widget.setParent(self._stacked_widget)
        widget.setProperty('color', self._icon_color)
        self._stacked_widget.addWidget(widget)

    # def visual_update(self, collapse=True):
    #     """
    #     Updates visual based on opened or closed state
    #     :param collapse: bool
    #     """
    #
    #     print('updating visuals ....')
    #
    # def update_display_button(self):
    #     """
    #     Updates the display button based on number of widgets in the stack
    #     """
    #
    #     self.set_displays(self.count())
    #
    # def set_displays(self, displays):
    #     """
    #     Sets displays
    #     :param displays: list
    #     """
    #
    #     if displays in [ToolsetDisplays.Single, ToolsetDisplays.Double, ToolsetDisplays.Triple]:
    #         self._display_mode_button.set_displays(displays)
    #     else:
    #         tpDcc.logger.error('setDisplays() must be 2 or 3')
    #
    # def block_save(self, flag):
    #     """
    #     Sets whether data saving is enabled or not
    #     :param flag: bool
    #     """
    #
    #     self._block_save = flag
    #
    # def set_active(self, active=True, emit=True):
    #     """
    #     Sets whether toolset widget is active or not
    #     :param active: bool
    #     :param emit: bool
    #     """
    #
    #     if active:
    #         self.expand(emit)
    #     else:
    #         self.collapse(emit)
    #     self.visual_update(collapse=not active)
    #
    # def set_current_index(self, index):
    #
    #     self.block_save(True)
    #
    #     for i in range(self._stacked_widget.count()):
    #         w = self._stacked_widget.widget(i)
    #         w.setSizePolicy(w.sizePolicy().horizontalPolicy(), QSizePolicy.Ignored)
    #
    #     self._stacked_widget.setCurrentIndex(index)
    #
    #     widget = self._stacked_widget.widget(index)
    #     if widget:
    #         widget.setSizePolicy(widget.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)
    #     else:
    #         tpDcc.logger.warning('Widget not found!')
    #
    #     self.block_save(False)
    #
    # def set_icon_color(self, color=(255, 255, 255), set_color=True):
    #     """
    #     Sets the icon color for all the icons
    #     :param color: tuple(int, int, int), color in RGB integer values in 0-255 range
    #     :param set_color: bool, saves current color overwriting cache variable
    #     """
    #
    #     if set_color:
    #         self._icon_color = color
    #     darken = 0.8
    #     self.set_item_icon_color(color)
    #     self._display_mode_button.set_icon_color(color)
    #     self._help_button.set_icon_color((color[0] * darken, color[1] * darken, color[2] * darken))
    #     self._title_frame.delete_button.set_icon_color(color)

    # def linked_properties(self, widget):
    #     """
    #     Returns list of linkable properties from widgets children
    #     :param widget:  list
    #     :return:
    #     """
    #
    #     for attr in widget.__dict__:
    #         if type(getattr(widget, attr)) in
    #
    # def auto_link_properties(self, widgets):
    #     """
    #     Add link properties if allowed
    #     :param widgets: list
    #     """
    #
    #     if not self.CONFIG.get('auto_link_properties', True):
    #         return
    #
    #     new_properties = list()
    #     names = list()
    #     for link_property in self._linked


class ToolsetDisplays(object):
    """
    Display modes for the toolset widget items
    """

    Single = 1
    Double = 2
    Triple = 3


class DisplayModeButton(buttons.BaseMenuButton, object):

    FIRST_INDEX = 1
    LAST_INDEX = -1

    clicked = Signal(object)

    def __init__(self, parent=None, size=16, color=(255, 255, 255), initial_index=FIRST_INDEX):
        super(DisplayModeButton, self).__init__(parent=parent)

        self._current_icon = None
        self._icons = None
        self._displays = None
        self._initial_display = initial_index
        self._current_size = size
        self._icon_color = color
        self._highlight_offset = 40

        self.setIconSize(QSize(size, size))
        self.set_displays(ToolsetDisplays.Double)

    def set_displays(self, displays=ToolsetDisplays.Triple):
        """
        Sets the number of displays
        :param displays:
        """

        self._displays = displays
        self.show()
