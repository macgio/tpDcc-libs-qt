#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle tools
"""

from __future__ import print_function, division, absolute_import

import webbrowser

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs.python import color
from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import stack, buttons


class ToolsetWidget(stack.StackItem, object):

    ID = 'toolsetID'
    CONFIG = None
    EXTENSION = 'toolset'

    StartLargets = -1
    StartSmallest = 0

    displaySwitched = Signal()
    updatedPropertyRequested = Signal()
    savePropertyRequested = Signal()
    windowClosed = Signal()
    toolsetClosed = Signal()
    toolsetHidden = Signal()
    toolsetShown = Signal()
    toolsetDragged = Signal()
    toolsetDropped = Signal()
    toolsetDragCancelled = Signal()
    toolsetActivated = Signal()
    toolsetDeactivated = Signal()

    def __init__(self, tree_widget=None, icon_color=(255, 255, 255), widget_item=None, parent=None, *args, **kwargs):

        self._block_save = False
        self._show_warnings = True
        self._icon = self.CONFIG.get('icon') if self.CONFIG else None
        self._icon_color = icon_color
        self._tree_widget = tree_widget
        self._toolset_widget_item = widget_item
        self._stacked_widget = None
        self._display_mode_button = None
        self._help_button = None
        self._settings_button = None
        self._connect_button = None
        self._widgets = list()
        self._attacher = None
        self._client = None
        self._dev = kwargs.get('dev', False)
        self._supported_dccs = self.CONFIG.get('supported_dccs', dict()) if self.CONFIG else dict()
        title = self.CONFIG.data.get('label', '') if self.CONFIG else ''
        collapsable = kwargs.get('collapsable', True)
        show_item_icon = kwargs.get('show_item_icon', True)

        super(ToolsetWidget, self).__init__(
            title=title, collapsed=True, icon=self._icon, shift_arrows_enabled=False, title_editable=False,
            parent=parent or tree_widget, collapsable=collapsable, show_item_icon=show_item_icon,
            delete_button_enabled=True if tree_widget else False,
        )

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def stacked_widget(self):
        return self._stacked_widget

    @property
    def attacher(self):
        return self._attacher

    @property
    def dev(self):
        return self._dev

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

        self.setContentsMargins(0, 0, 0, 0)
        self._contents_layout.setContentsMargins(0, 0, 0, 0)
        self._contents_layout.setSpacing(0)

        self._stacked_widget = QStackedWidget(self._widget_hider)
        self._stacked_widget.setContentsMargins(0, 0, 0, 0)
        self._stacked_widget.setLineWidth(0)
        self._contents_layout.addWidget(self._stacked_widget)

        self.show_expand_indicator(False)
        self.set_title_text_mouse_transparent(True)

        self._display_mode_button = DisplayModeButton(color=self._icon_color, size=16, parent=self)
        self._display_mode_button.setFixedSize(QSize(22, 22))
        self._connect_button = buttons.BaseToolButton(parent=self).image('connect').icon_only()
        self._connect_button.setFixedSize(QSize(22, 22))
        self._connect_button.setEnabled(False)
        self._connect_button.setToolTip('No connected to any DCC')
        self._help_button = buttons.BaseMenuButton(parent=self)
        self._help_button.set_icon(tpDcc.ResourcesMgr().icon('help'))
        self._help_button.setFixedSize(QSize(22, 22))
        self._settings_button = buttons.BaseMenuButton(parent=self)
        self._settings_button.set_icon(tpDcc.ResourcesMgr().icon('settings'))
        self._settings_button.setFixedSize(QSize(22, 22))

        # TODO: Disable until we implement preferences system
        # self._settings_button.setVisible(False)

        # We call if after setting all buttons
        self.set_icon_color(self._icon_color)

        self.visual_update(collapse=True)

        self._dccs_menu = QMenu(self)

        display_button_pos = 7
        self._title_frame.horizontal_layout.insertWidget(display_button_pos - 1, self._help_button)
        self._title_frame.horizontal_layout.insertWidget(display_button_pos - 2, self._settings_button)
        self._title_frame.horizontal_layout.insertWidget(0, self._connect_button)
        self._title_frame.horizontal_layout.insertWidget(display_button_pos, self._display_mode_button)
        self._title_frame.horizontal_layout.setSpacing(0)
        self._title_frame.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self._title_frame.delete_button.setIconSize(QSize(12, 12))
        self._title_frame.item_icon_button.setIconSize(QSize(20, 20))

        font = QFont()
        font.setBold(True)
        self.setFont(font)

    def setup_signals(self):
        super(ToolsetWidget, self).setup_signals()

        self._title_frame.mouseReleaseEvent = self._on_activate_event

        if self._toolset_widget_item:
            self._display_mode_button.clicked.connect(self._toolset_widget_item.set_current_index)
            self._display_mode_button.clicked.connect(lambda: self.displaySwitched.emit())
            self.displaySwitched.connect(lambda: self.updateRequested.emit())

        self._help_button.leftClicked.connect(self._on_open_help)
        self._settings_button.leftClicked.connect(self._on_show_preferences_dialog)

        self.deletePressed.connect(self._on_stop_callbacks)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_attacher(self, attacher):
        """
        Sets attacher of this toolset
        The attacher is the window this toolset belongs to. Can be a custom Qt window or Hub
        :param attacher:
        """

        self._attacher = attacher

    def get_icon(self):
        """
        Returns toolset icon
        :return: QIcon
        """

        if not self._title_frame:
            return tpDcc.ResourcesMgr().icon('tpdcc')

        return tpDcc.ResourcesMgr().icon(self._title_frame.item_icon or 'tpdcc')

    def widgets(self):
        """
        Returns all display widgets
        :return: list
        """

        return self._widgets

    def display_index(self):
        """
        Current index of the stacked widget
        :return: int
        """

        return self._stacked_widget.currentIndex()

    def current_widget(self):
        """
        Returns current active widget
        :return: QWidget
        """

        return self.widgets()[self.display_index()]

    def widget_at(self, index):
        """
        Returns stacked widget at given index
        :param index: int
        :return: QWidget
        """

        return self._stacked_widget.widget(index)

    def count(self):
        """
        Returns the total amount of widgets added to the stack
        :return: int
        """

        return self._stacked_widget.count()

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
        widget.setProperty('color', self._icon_color)
        self._stacked_widget.addWidget(widget)

    def visual_update(self, collapse=True):
        """
        Updates visual based on opened or closed state
        :param collapse: bool
        """

        if collapse:
            self.set_icon_color(color.desaturate(self._icon_color, 0.75), set_color=False)
            self.title_text_widget().setObjectName('disabled')
        else:
            self.set_icon_color(self._icon_color)
            self.title_text_widget().setObjectName('active')

        qtutils.update_widget_style(self.title_text_widget())

        self.setUpdatesEnabled(False)
        self.updatedPropertyRequested.emit()
        self.setUpdatesEnabled(True)

    def update_display_button(self):
        """
        Updates the display button based on number of widgets in the stack
        """

        self.set_displays(self.count())

    def set_displays(self, displays):
        """
        Sets displays
        :param displays: list
        """

        if displays in [ToolsetDisplays.Single, ToolsetDisplays.Double, ToolsetDisplays.Triple]:
            self._display_mode_button.set_displays(displays)
        else:
            tpDcc.logger.error('setDisplays() must be 2 or 3')

    def block_save(self, flag):
        """
        Sets whether data saving is enabled or not
        :param flag: bool
        """

        self._block_save = flag

    def set_active(self, active=True, emit=True):
        """
        Sets whether toolset widget is active or not
        :param active: bool
        :param emit: bool
        """

        if active:
            self.expand(emit)
        else:
            self.collapse(emit)
        self.visual_update(collapse=not active)

    def set_current_index(self, index):

        self.block_save(True)

        for i in range(self._stacked_widget.count()):
            w = self._stacked_widget.widget(i)
            w.setSizePolicy(w.sizePolicy().horizontalPolicy(), QSizePolicy.Ignored)

        self._stacked_widget.setCurrentIndex(index)

        widget = self._stacked_widget.widget(index)
        if widget:
            widget.setSizePolicy(widget.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)
        else:
            tpDcc.logger.warning('Widget not found!')

        self.block_save(False)

    def set_icon_color(self, color=(255, 255, 255), set_color=True):
        """
        Sets the icon color for all the icons
        :param color: tuple(int, int, int), color in RGB integer values in 0-255 range
        :param set_color: bool, saves current color overwriting cache variable
        """

        if set_color:
            self._icon_color = color
        darken = 0.8
        self.set_item_icon_color(color)
        self._display_mode_button.set_icon_color(color)
        self._help_button.set_icon_color((color[0] * darken, color[1] * darken, color[2] * darken))
        self._title_frame.delete_button.set_icon_color(color)

    def populate_widgets(self):

        property_widgets = self.property_widgets()

        # self.savePropertyRequested.connect(self.save_properties)
        # self.updatedPropertyRequested.connect(self.update_properties)

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
    def auto_link_properties(self, widgets):
        """
        Add link properties if allowed
        :param widgets: list
        """

        if not self.CONFIG and self.CONFIG.get('auto_link_properties', True):
            return

        new_properties = list()
        names = list()
        # for link_property in self._linked

    def property_widgets(self, widget=None, current_widget=False):
        """
        Get properties widgets from the stack
        :param widget: QWidget
        :param current_widget: bool, Set True to only search the current active widget in the stack
        :return:
        """

        result = list()

        if current_widget:
            widget = widget or self._stacked_widget.current_widget()
        else:
            widget = widget or self._stacked_widget

        for child in qtutils.iterate_children(widget, skip='skipChildren'):
            if child.property('prop') is not None:
                result.append(child)

        return result

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _stop_selection_callback(self):
        print('Stop Selection Callbacks ...')

    def _reset_connect_button(self):
        self._connect_button.setEnabled(False)
        self._connect_button.setToolTip('No connected to any DCC')

    def _update_client(self):
        if not self._client:
            return

        valid_connect = self._client.connect()
        if not valid_connect:
            self._reset_connect_button()
            return False

        success, dcc_exe = self._client.update_paths()
        if not success:
            tpDcc.logger.warning('Error while connecting to Dcc: update paths ...')
            self._reset_connect_button()
            return False

        success = self._client.update_dcc_paths(dcc_exe)
        if not success:
            tpDcc.logger.warning('Error while connecting to Dcc: update dcc paths ...')
            self._reset_connect_button()
            return False

        success = self._client.init_dcc()
        if not success:
            tpDcc.logger.warning('Error while connecting to Dcc: init dcc ...')
            self._reset_connect_button()
            return False

        dcc_name, dcc_version = self._client.get_dcc_info()
        if not dcc_name or not dcc_version:
            tpDcc.logger.warning(
                'Error while connecting to Dcc: get dcc info ... ({}, {})'.format(dcc_name, dcc_version))
            self._reset_connect_button()
            return False

        if dcc_name not in self._supported_dccs:
            tpDcc.logger.warning('Connected DCC {} ({}) is not supported!'.format(dcc_name, dcc_version))
            self._reset_connect_button()
            return False

        supported_versions = self._supported_dccs[dcc_name]
        if dcc_version not in supported_versions:
            tpDcc.logger.warning('Connected DCC {} is supported but version {} is not!'.format(dcc_name, dcc_version))
            self._reset_connect_button()
            return False

        self._connect_button.setEnabled(True)
        self._connect_button.setToolTip('Connected to: {} ({})'.format(dcc_name, dcc_version))

        return True

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_activate_event(self, event, emit=True):
        self._on_toggle_contents(emit=emit)
        event.ignore()

    def _on_open_help(self):
        """
        Internal callback function that is called when help button is clicked
        """

        url = self.CONFIG.get('help_url', '') if self.CONFIG else ''
        if not url:
            return
        webbrowser.open(url)

    def _on_stop_callbacks(self):
        self._stop_selection_callback()

    def _on_show_preferences_dialog(self):
        tpDcc.logger.info('Preferences functionality not implemented yet!')
        # from tpDcc.libs.qt.widgets import lightbox
        # from tpDcc.libs.qt.core import preferences
        # self._lightbox = lightbox.Lightbox(self)
        # self._lightbox.closed.connect(self._on_close_lightbox)
        # self._preferences_window = preferences.PreferencesWidget(settings=self.preferences_settings())
        # self._preferences_window.setFixedHeight(500)
        # self._preferences_window.closed.connect(self._on_close_preferences_window)
        # self._lightbox.set_widget(self._preferences_window)
        # for pref_widget in self._preference_widgets_classes:
        #     pref_widget = pref_widget()
        #     self._preferences_window.add_category(pref_widget.CATEGORY, pref_widget)
        # self._theme_widget = self._setup_theme_preferences()
        # self._preferences_window.add_category(self._theme_widget.CATEGORY, self._theme_widget)
        # self._lightbox.show()

    def _on_close_preferences_window(self, save_widget=False):
        self._on_close_lightbox(save_widget)
        self._lightbox.blockSignals(True)
        self._lightbox.close()
        self._lightbox.blockSignals(False)

    def _on_close_lightbox(self, save_widgets=False):
        if not save_widgets:
            self._settings_accepted(**self._theme_widget._dlg._form_widget.default_values())
        else:
            self._settings_accepted(**self._theme_widget._dlg._form_widget.values())

    def _on_dcc_disconnected(self):
        self._connect_button.setEnabled(False)
        self._connect_button.setToolTip('No connected to any DCC')


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

        menu_icon_double_names = ['menu_double_empty', 'menu_double_one', 'menu_double_full']
        menu_icon_triple_names = ['menu_triple_empty', 'menu_triple_one', 'menu_triple_two', 'menu_triple_full']
        self._menu_icon_double = [tpDcc.ResourcesMgr().icon(menu_icon) for menu_icon in menu_icon_double_names]
        self._menu_icon_triple = [tpDcc.ResourcesMgr().icon(menu_icon) for menu_icon in menu_icon_triple_names]

        self._current_icon = None
        self._icons = None
        self._displays = None
        self._initial_display = initial_index
        self._current_size = size
        self._icon_color = color
        self._highlight_offset = 40

        self.setIconSize(QSize(size, size))
        self.set_displays(ToolsetDisplays.Double)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mouseReleaseEvent(self, event):
        """
        Overrides base QWidget mouseReleaseEvent
        :param event: QMouseEvent
        """

        new_icon, new_index = self.next_icon()
        self.set_icon(new_icon, size=self._current_size, colors=self._icon_color)
        self._current_icon = new_icon
        self.clicked.emit(new_index - 1)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_displays(self, displays=ToolsetDisplays.Triple):
        """
        Sets the number of displays
        :param displays:
        """

        self._displays = displays
        self.show()

        if displays == 3:
            self._icons = self._menu_icon_triple
        elif displays == 2:
            self._icons = self._menu_icon_double
        elif displays == 1:
            self.hide()
        else:
            tpDcc.logger.error('only 2 or 3 displays are available!')

        self._current_icon = self._icons[self._initial_display]
        self.set_icon_index(self._initial_display)

    def set_icon_index(self, index, size=None, color=None):
        """
        Sets icon by its display index
        :param index: int
        :param size:
        :param color:
        """

        if size is None:
            size = self._current_size
        if color is None:
            color = self._icon_color

        self.set_icon(self._icons[index], size=size, colors=color)

    def next_icon(self):
        """
        Returns next icon of the current one and its index
        :return: tuple(QIcon, int)
        """

        new_index = max((self._icons.index(self._current_icon) + 1) % len(self._icons), 1)
        new_icon = self._icons[new_index]

        return new_icon, new_index
