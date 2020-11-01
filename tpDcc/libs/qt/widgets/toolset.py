#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager to handle tools
"""

from __future__ import print_function, division, absolute_import

import os
import logging
import webbrowser

from Qt.QtCore import Qt, Signal, QSize
from Qt.QtWidgets import QApplication, QSizePolicy, QMenu, QFrame, QPlainTextEdit, QDialog
from Qt.QtGui import QCursor, QPixmap, QFont

from tpDcc import dcc
from tpDcc.managers import resources
from tpDcc.libs.python import python, color
from tpDcc.libs.qt.core import qtutils, base, preferences
from tpDcc.libs.qt.widgets import layouts, label, stack, buttons, switch, gif, dividers, theme

LOGGER = logging.getLogger('tpDcc-libs-qt')


class ToolsetPropertiesDict(python.ObjectDict, object):

    def update(self, others, convert_dict=False):
        """
        Updates dicts found in the item as well
        :param others: dict, dictionary to update this object with
        :param convert_dict: bool, Convert the dictionaries in others items to ToolsetPropertyDict
        """

        if convert_dict:
            for k, d in others.items():
                others[k] = ToolsetPropertiesDict(**d) if type(d) == dict else others[k]

        super(ToolsetPropertiesDict, self).update(others)


class ToolsetWidget(stack.StackItem, object):

    ID = 'toolsetID'
    CONFIG = None
    EXTENSION = 'toolset'

    StartLargest = -1
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
    helpModeChanged = Signal(bool)

    def __init__(self, tree_widget=None, icon_color=(255, 255, 255), widget_item=None, parent=None, *args, **kwargs):

        self._block_save = False
        self._show_warnings = True
        self._icon = self.CONFIG.get('icon') if self.CONFIG else None
        self._icon_color = icon_color
        self._tree_widget = tree_widget
        self._toolset_widget_item = widget_item
        self._stacked_widget = None
        self._prev_stack_index = 1
        self._display_mode_button = None
        self._manual_button = None
        self._help_button = None
        self._help_widget = None
        self._settings_button = None
        self._connect_button = None
        self._widgets = list()
        self._attacher = None
        self._client = None
        self._help_mode = False
        self._help_event = None
        self._dev = kwargs.get('dev', False)
        self._supported_dccs = self.CONFIG.get('supported_dccs', dict()) if self.CONFIG else dict()
        self._properties = self._setup_properties()
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

    @property
    def properties(self):
        return self._properties

    @property
    def info_mode(self):
        return self._help_mode

    # =================================================================================================================
    # TO OVERRIDE
    # =================================================================================================================

    def initialize_properties(self):
        """
        Initializes properties of the toolset widget
        :return: list
        """

        return list()

    def setup_client(self):
        """
        Function that is called to setup the client of the application
        Override in specific toolset widgets
        """

        pass

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

    def help_mode(self, flag):
        """
        Function that can be used to show custom tooltip widgets for current toolset
        Override in specific toolset widgets
        :param flag: bool, Whether or not help mode is enabled
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

        self._stacked_widget = stack.SlidingOpacityStackedWidget(self._widget_hider)
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
        self._manual_button = buttons.BaseMenuButton(parent=self)
        self._manual_button.set_icon(resources.icon('manual'))
        self._manual_button.setFixedSize(QSize(22, 22))
        self._help_button = buttons.BaseMenuButton(parent=self)
        self._help_button.set_icon(resources.icon('help'))
        self._help_button.setFixedSize(QSize(22, 22))
        self._help_switch = switch.SwitchWidget(parent=self)
        self._settings_button = buttons.BaseMenuButton(parent=self)
        self._settings_button.set_icon(resources.icon('settings'))
        self._settings_button.setFixedSize(QSize(22, 22))
        self._help_widget = ToolsetHelpWidget()

        self._preferences_widget = preferences.PreferencesWidget(parent=self)
        self._stacked_widget.addWidget(self._preferences_widget)

        # We call if after setting all buttons
        self.set_icon_color(self._icon_color)

        self.visual_update(collapse=True)

        self._dccs_menu = QMenu(self)

        display_button_pos = 7
        self._title_frame.horizontal_layout.insertWidget(display_button_pos - 1, self._manual_button)
        self._title_frame.horizontal_layout.insertWidget(display_button_pos - 1, self._help_switch)
        self._title_frame.horizontal_layout.insertWidget(display_button_pos - 1, self._help_button)
        self._title_frame.horizontal_layout.insertWidget(display_button_pos - 1, self._settings_button)
        self._title_frame.horizontal_layout.insertWidget(0, self._connect_button)
        self._title_frame.horizontal_layout.insertWidget(display_button_pos, self._display_mode_button)
        self._title_frame.horizontal_layout.setSpacing(0)
        self._title_frame.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self._title_frame.delete_button.setIconSize(QSize(12, 12))
        self._title_frame.item_icon_button.setIconSize(QSize(20, 20))

        font = QFont()
        font.setBold(True)
        self.setFont(font)

        if not dcc.is_standalone():
            self._connect_button.setVisible(False)

    def setup_signals(self):
        super(ToolsetWidget, self).setup_signals()

        self._title_frame.mouseReleaseEvent = self._on_activate_event

        if self._toolset_widget_item:
            self._display_mode_button.clicked.connect(self._toolset_widget_item.set_current_index)
            self._display_mode_button.clicked.connect(lambda: self.displaySwitched.emit())
            self.displaySwitched.connect(lambda: self.updateRequested.emit())

        self._manual_button.leftClicked.connect(self._on_open_help)
        self._help_button.leftClicked.connect(self._on_toggle_info_switch)
        self._help_switch.toggled.connect(self._on_toggle_help_mode)
        self._settings_button.leftClicked.connect(self._on_show_preferences_dialog)
        self._preferences_widget.closed.connect(self._on_close_preferences_window)

        self.deletePressed.connect(self._on_stop_callbacks)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def initialize(self):
        self.setup_client()
        self.pre_content_setup()
        toolset_contents = self.contents()
        for toolset_widget in toolset_contents:
            self.add_stacked_widget(toolset_widget)
        if self.count() > 0:
            self._stacked_widget.setCurrentIndex(1)
        self.post_content_setup()
        self.update_display_button()
        self.expand()

    def set_attacher(self, attacher):
        """
        Sets attacher of this toolset
        The attacher is the window this toolset belongs to. Can be a custom Qt window or Hub
        :param attacher:
        """

        self._attacher = attacher

        # Setup standard settings and attacher preferences
        self._preferences_widget.set_settings(self._attacher.settings())
        self._theme_prefs_widget = theme.ThemePreferenceWidget(
            theme=self._attacher.theme(), parent=self._preferences_widget)
        self._preferences_widget.add_category(self._theme_prefs_widget.CATEGORY, self._theme_prefs_widget)

        # self.setup_attacher_settings(attacher)

        self._attacher.themeUpdated.connect(self.reload_theme)
        self._attacher.styleReloaded.connect(self.reload_theme)

        self.reload_theme(self._attacher.theme())

    def setup_attacher_settings(self, attacher):
        """
        Function that can be used to setup all the attacher settings widgets
        :return:
        """

        if not attacher:
            return

        if not hasattr(attacher, 'get_settings_widgets') or not callable(attacher.get_settings_widgets):
            return

        settings_widgets = attacher.get_settings_widgets()
        if not settings_widgets:
            return

    def get_icon(self):
        """
        Returns toolset icon
        :return: QIcon
        """

        if not self._title_frame:
            return resources.icon('tpdcc')

        return resources.icon(self._title_frame.item_icon or 'tpdcc')

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

        # We ignore first widget, which is the preferences widget

        return self._stacked_widget.count() - 1

    def item_at(self, index):
        """
        Returns widget located in given index of the toolset stack
        :param index: int
        :return: QWidget or None
        """

        return self._stacked_widget.widget(index)

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
        widget.setParent(self._widget_hider)
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
            LOGGER.error('setDisplays() must be 2 or 3')

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
            LOGGER.warning('Widget not found!')

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
        self._manual_button.set_icon_color((color[0] * darken, color[1] * darken, color[2] * darken))
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

    def reload_theme(self, theme):
        if not theme:
            return
        stylesheet = theme.stylesheet()
        self.setStyleSheet(stylesheet)

        # cached_icons_keys = icon.IconCache._resources_keys_cache.copy()
        # keys_names_mapping = icon.IconCache._resources_names_keys_mapping
        #
        # print('gogogog')
        #
        # # Update icons taking into account the new theme
        # new_icons_to_apply = dict()
        # for icon_key, icon_object in cached_icons_keys.items():
        #     icon_full_name = keys_names_mapping.get(icon_key, None)
        #     if not icon_full_name:
        #         continue
        #     icon_name, icon_ext = os.path.splitext(icon_full_name)
        #     new_icon = resources.icon(icon_name, extension=icon_ext, theme=theme.name())
        #     if not new_icon or new_icon.isNull():
        #         continue
        #     new_icons_to_apply[icon_key] = new_icon
        #
        # # TODO: This can by quite hard to process. Find a better approach for this
        # all_widgets = self.findChildren(QWidget)
        # for w in all_widgets:
        #     if hasattr(w, 'setIcon'):
        #         try:
        #             curr_icon = w.icon()
        #             curr_icon_key = curr_icon.cacheKey()
        #             if curr_icon_key not in new_icons_to_apply:
        #                 continue
        #             w.setIcon(new_icons_to_apply[curr_icon_key])
        #         except Exception:
        #             pass

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _setup_properties(self, properties=None):

        tool_props = properties or self.initialize_properties()
        instance_props = ToolsetPropertiesDict()
        for prop in tool_props:
            instance_props[prop['name']] = ToolsetPropertiesDict(**prop)
            if 'default' not in instance_props[['name']]:
                instance_props[prop['name']].default = instance_props[prop['name']].value

        return instance_props

    def _stop_selection_callback(self):
        print('Stop Selection Callbacks ...')

    def _reset_connect_button(self, text='No connected to any DCC', severity='warning'):
        self._connect_button.setEnabled(False)
        self._connect_button.setToolTip(str(text))

        if severity == 'warning':
            LOGGER.warning(text)
            self._connect_button.setStyleSheet('background-color: #bc3030')
        elif severity == 'error':
            LOGGER.error(text)
            self._connect_button.setStyleSheet('background-color: #e4c019')
        else:
            LOGGER.info(text)
            self._connect_button.setStyleSheet('')

    def _update_client(self):
        if not self._client:
            return

        valid_connect = self._client.connect()
        if not valid_connect:
            self._reset_connect_button()
            return False

        if dcc.is_standalone():

            success, dcc_exe = self._client.update_paths()
            if not success:
                self._reset_connect_button('Error while connecting to Dcc: update paths ...', severity='error')
                return False

            success = self._client.update_dcc_paths(dcc_exe)
            if not success:
                self._reset_connect_button('Error while connecting to Dcc: update dcc paths ...', severity='error')
                return False

            success = self._client.init_dcc()
            if not success:
                self._reset_connect_button('Error while connecting to Dcc: init dcc ...', severity='error')
                return False

        dcc_name, dcc_version = self._client.get_dcc_info()
        if not dcc_name or not dcc_version:
            self._reset_connect_button(
                'Error while connecting to Dcc: get dcc info ... ({}, {})'.format(dcc_name, dcc_version),
                severity='error')
            return False

        if dcc_name not in self._supported_dccs:
            self._reset_connect_button(
                'Connected DCC {} ({}) is not supported!'.format(dcc_name, dcc_version), severity='warning')
            return False

        supported_versions = self._supported_dccs[dcc_name]
        if dcc_version not in supported_versions:
            self._reset_connect_button(
                'Connected DCC {} is supported but version {} is not!'.format(dcc_name, dcc_version),
                severity='warning')
            return False

        self._connect_button.setEnabled(True)
        msg = 'Connected to: {} ({})'.format(dcc_name, dcc_version)
        self._connect_button.setToolTip(msg)
        LOGGER.info(msg)

        if not dcc.is_standalone():
            self._connect_button.setVisible(False)

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

    def _on_toggle_info_switch(self):
        self._help_switch.setChecked(not self._help_switch.isChecked())

    def _on_toggle_help_mode(self, flag):
        """
        Internal callback function that toggles info mode
        """

        self._help_mode = flag

        if not self._help_event:
            self._help_event = self.help_mode(self._help_mode)

        if self._help_event:
            if self._help_mode:
                self._help_event.help_mode = True
            else:
                self._help_event.help_mode = False
                self._help_event.current_tooltip.close()
                self._help_event.close()
                self._help_event = None

        self.helpModeChanged.emit(self._help_mode)

    def _on_stop_callbacks(self):
        self._stop_selection_callback()

    def _on_show_preferences_dialog(self):
        if not self._attacher:
            return

        self._prev_stack_index = self._stacked_widget.currentIndex()
        self._stacked_widget.setCurrentIndex(0)

    def _on_close_preferences_window(self, *args):
        self._stacked_widget.setCurrentIndex(self._prev_stack_index)
        if self._attacher:
            self.reload_theme(self._attacher.theme())

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
        self._menu_icon_double = [resources.icon(menu_icon) for menu_icon in menu_icon_double_names]
        self._menu_icon_triple = [resources.icon(menu_icon) for menu_icon in menu_icon_triple_names]

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
            LOGGER.error('only 2 or 3 displays are available!')

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


class ToolsetHelpWidget(base.BaseFrame, object):
    def __init__(self, parent=None):
        super(ToolsetHelpWidget, self).__init__(parent=parent)

    def ui(self):
        super(ToolsetHelpWidget, self).ui()

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)

        self._image_label = label.BaseLabel(parent=self)
        self._title_label = label.BaseLabel(parent=self).strong()
        self._description_text = QPlainTextEdit(parent=self)
        # self._description_text.setFrameShape(QFrame.NoFrame)
        self._description_text.setMinimumWidth(200)
        self._description_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._gif_label = gif.GifLabel(parent=self)
        self._gif_label.set_size(256, 256)

        self.main_layout.addWidget(self._title_label)
        self.main_layout.addWidget(dividers.Divider())
        body_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        body_layout.addWidget(self._description_text)
        body_layout.addWidget(self._gif_label)
        body_layout.addWidget(self._image_label)
        body_layout.addStretch()
        self.main_layout.addLayout(body_layout)

    def set_title(self, title):
        self._title_label.setText(str(title))

    def set_description(self, description):
        self._description_text.setPlainText(str(description))

    def set_image(self, image_file):
        if not image_file or not os.path.isfile(image_file):
            return
        self._image_label.setPixmap(QPixmap(image_file).scaled(QSize(256, 256), Qt.KeepAspectRatio))
        self._image_label.setVisible(True)
        self._gif_label.setVisible(False)

    def set_gif(self, gif_file):
        if not gif_file or not os.path.isfile(gif_file):
            return
        self._gif_label.set_file(gif_file)
        self._gif_label.setVisible(True)
        self._image_label.setVisible(False)


class ToolsetHelpEvent(base.BaseWidget, object):
    def __init__(self, layout, widgets=None, tooltip_widget=None):
        super(ToolsetHelpEvent, self).__init__()

        self._widgets = python.force_list(widgets)
        self._help_mode = False
        self._current_tooltip = ToolsetTooltipHelpDialog(self, tooltip_widget)
        self._current_widget = None
        self.setVisible(False)

        layout.insertWidget(0, self)

        for widget in self._widgets:
            widget.installEventFilter(self)

    @property
    def help_mode(self):
        return self._help_mode

    @help_mode.setter
    def help_mode(self, flag):
        self._help_mode = flag

    @property
    def current_tooltip(self):
        return self._current_tooltip

    def eventFilter(self, obj, event):
        pos = QCursor.pos()
        widget_under_cursor = QApplication.widgetAt(pos)
        if not widget_under_cursor or widget_under_cursor.objectName() == '':
            self._current_tooltip.hide()
            return super(ToolsetHelpEvent, self).eventFilter(obj, event)

        if self._help_mode:
            self._current_tooltip.move(pos.x() + 15, pos.y())
            if self._current_widget != widget_under_cursor:
                self._current_widget = widget_under_cursor
                tooltip_data = self._current_widget.property('tooltip_help')
                self._current_tooltip.update_tooltip(tooltip_data)
        else:
            self._current_tooltip.hide()

        return super(ToolsetHelpEvent, self).eventFilter(obj, event)


class ToolsetTooltipHelpDialog(QDialog, object):
    def __init__(self, parent, tooltip_widget):
        super(ToolsetTooltipHelpDialog, self).__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self._tooltip_widget = tooltip_widget
        self._layout = layouts.VerticalLayout(margins=(0, 0, 0, 0))
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._tooltip_widget)
        self.setLayout(self._layout)
        self._tooltip_data = None
        self.setStyleSheet('QDialog{background: rgb(60, 70, 75);}')

    def update_tooltip(self, tooltip_data):
        self._tooltip_data = tooltip_data
        if not self._tooltip_data:
            self.hide()
            return

        title = tooltip_data.get('title', '')
        description = tooltip_data.get('description', '')
        image_file = tooltip_data.get('image', None)
        gif_file = tooltip_data.get('gif', None)

        self._tooltip_widget.set_title(title)
        self._tooltip_widget.set_description(description)
        self._tooltip_widget.set_image(image_file)
        self._tooltip_widget.set_gif(gif_file)

        self.show()
