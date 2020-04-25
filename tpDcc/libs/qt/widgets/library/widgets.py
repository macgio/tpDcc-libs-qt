#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different widgets used in libraries
"""

from __future__ import print_function, division, absolute_import

import traceback
from functools import partial
from collections import OrderedDict

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs import qt
from tpDcc.libs.qt.core import animation, image, icon, qtutils, color, pixmap, statusbar
from tpDcc.libs.qt.widgets import progressbar, toolbar, action, buttons

logger = tpDcc.LogsMgr().get_logger()


class LibraryImageSequenceWidget(QToolButton, object):

    DEFAULT_PLAYHEAD_COLOR = QColor(255, 255, 255, 220)
    DEFAULT_PLAYHEAD_HEIGHT = 4

    DEFAULT_STYLE = ("\n"
                     "    QToolBar{\n"
                     "    border: 0px solid black; \n"
                     "    border-radius:2px;\n"
                     "    background-color: rgb(0,0,0,100);\n"
                     "    }\n"
                     "    QToolButton{\n"
                     "    background-color: transparent;\n"
                     "    }\n"
                     "    ")

    def __init__(self, *args):
        super(LibraryImageSequenceWidget, self).__init__(*args)

        self.setMouseTracking(True)

        self._image_sequence = image.ImageSequence('')
        self._image_sequence.frameChanged.connect(self._on_frame_changed)

        self._toolbar = QToolBar(self)
        self._toolbar.setStyleSheet(self.DEFAULT_STYLE)
        animation.fade_out_widget(self._toolbar, duration=0)

        spacer = QWidget()
        spacer.setMaximumWidth(4)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._toolbar.addWidget(spacer)

        spacer1 = QWidget()
        spacer1.setMaximumWidth(4)
        spacer1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._first_spacer = self._toolbar.addWidget(spacer1)

        self.set_size(150, 150)

    def addAction(self, path, text, tip, callback):
        """
        Overrides base QToolButton addAction function
        Adds aan action to the toolbar
        :param path: str
        :param text: str
        :param tip: str
        :param callback: fn
        :return: QAction
        """

        action_icon = icon.Icon.state_icon(
            path,
            color='rgb(250,250,250,160)',
            color_active='rgb(250,250,250,250)',
            color_disabled='rgb(0,0,0,20)'
        )
        action = QAction(action_icon, text, self._toolbar)
        action.setToolTip(tip)
        self._toolbar.insertAction(self._first_spacer, action)
        action.triggered.connect(callback)

        return action

    def actions(self):
        """
        Overrides base QToolButton actions function
        Returns all the actions that are a child of the toolbar
        :return: list(QAction)
        """

        actions = list()
        for child in self._toolbar.children():
            if isinstance(child, QAction):
                actions.append(child)

        return actions

    def resizeEvent(self, event):
        """
        Overrides base QToolButton resizeEvent function
        Called when the widget is resized
        :param event: QResizeEvent
        """

        self.update_toolbar()

    def enterEvent(self, event):
        """
        Overrides base QToolButton enterEvent function
        Starts playing the image sequence when the mouse enters the widget
        :param event: QEvent
        """

        self._image_sequence.start()
        animation.fade_in_widget(self._toolbar, duration=300)

    def leaveEvent(self, event):
        """
        Overrides base QToolButton leaveEvent function
        Stops playing the image sequence when the mouse leaves the widget
        :param event: QEvent
        """

        self._image_sequence.pause()
        animation.fade_out_widget(self._toolbar, duration=300)

    def mouseMoveEvent(self, event):
        """
        Overrides base QToolButton mouseMoveEvent function
        :param event: QEvent
        """

        if qtutils.is_control_modifier() and self._image_sequence.frame_count() > 1:
            percent = 1.0 - (float(self.width() - event.pos().x()) / float(self.width()))
            frame = int(self._image_sequence.frame_count() * percent)
            self._image_sequence.jump_to_frame(frame)
            frame_icon = self._image_sequence.current_icon()
            self.setIcon(frame_icon)

    def paintEvent(self, event):
        """
        Overrides base QToolButton paintEvent function
        Triggered on frame changed
        :param event: QEvent
        """

        super(LibraryImageSequenceWidget, self).paintEvent(event)

        painter = QPainter()
        painter.begin(self)
        if self.current_filename() and self._image_sequence.frame_count() > 1:
            r = event.rect()
            playhead_height = self.playhead_height()
            playhead_pos = self._image_sequence.percent() * r.width() - 1
            x = r.x()
            y = self.height() - playhead_height
            painter.seten(Qt.NoPen)
            painter.setBrush(QBrush(self.DEFAULT_PLAYHEAD_COLOR))
            painter.drawRect(x, y, playhead_pos, playhead_height)

        painter.end()

    def set_path(self, path):
        """
        Sets a single frame image sequence
        :param path: str
        """

        self._image_sequence.set_path(path)
        self.update_icon()

    def set_dirname(self, dirname):
        """
        Sets the location of the image sequence
        :param dirname: str
        """

        self._image_sequence.set_dirname(dirname)
        self.update_icon()

    def current_filename(self):
        """
        Returns the current image location
        :return: str
        """

        return self._image_sequence.current_filename()

    def playhead_height(self):
        """
        Returns the height of the playhead
        :return: int
        """

        return self.DEFAULT_PLAYHEAD_COLOR

    def set_size(self, w, h):
        """
        Set the size of the widget and updates icon size at the same time
        :param w: int
        :param h: int
        """

        self._size = QSize(w, h)
        self.setIconSize(self._size)
        self.setFixedSize(self._size)

    def update_icon(self):
        """
        Updates the icon for the current frame
        """

        if self._image_sequence.frames():
            frame_icon = self._image_sequence.current_icon()
            self.setIcon(frame_icon)

    def update_toolbar(self):
        """
        Updates the toolbar size depending on the number of actions
        """

        self._toolbar.setIconSize(QSize(16, 20))
        count = len(self.actions()) - 3
        width = 26 * count
        self._toolbar.setGeometry(0, 0, width, 25)
        x = self.rect().center().x() - (self._toolbar.width() * 0.5)
        y = self.height() - self._toolbar.height() - 12
        self._toolbar.setGeometry(x, y, self._toolbar.width(), self._toolbar.height())

    def _on_frame_changed(self, frame=None):
        """
        Internal callback function triggered when the image sequence changes frame
        :param frame: int or None
        """

        if not qtutils.is_control_modifier():
            frame_icon = self._image_sequence.current_icon()
            self.setIcon(frame_icon)


class LibrarySearchWidget(QLineEdit, object):
    SPACE_OPEARTOR = 'and'
    PLACEHOLDER_TEXT = 'Search'

    searchChanged = Signal()

    def __init__(self, parent=None):
        super(LibrarySearchWidget, self).__init__(parent=parent)

        self._library = None
        self._space_operator = 'and'
        search_icon = tpDcc.ResourcesMgr().icon('search', theme='black')
        self._icon_btn = buttons.IconButton(search_icon, icon_padding=2, parent=self)
        self._icon_btn.clicked.connect(self._on_icon_clicked)
        self.set_icon(search_icon)
        cross_icon = tpDcc.ResourcesMgr().icon('delete', theme='black')
        self._clear_btn = buttons.IconButton(cross_icon, icon_padding=2, parent=self)
        self._clear_btn.setCursor(Qt.ArrowCursor)
        self._clear_btn.setToolTip('Clear all search text')
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self.setPlaceholderText(self.PLACEHOLDER_TEXT)
        self.textChanged.connect(self._on_text_changed)
        self.update()

        tip = 'Search all current items'
        self.setToolTip(tip)
        self.setStatusTip(tip)

        self.setStyleSheet('border-radius: 10px; padding-left: 2px; padding-right: 2px; border: 2px;')

    def update(self):
        """
        Overrides base QLineEdit update function
        """

        self.update_icon_color()
        self.update_clear_button()

    def resizeEvent(self, event):
        """
        Overrides base QLineEdit resizeEvent function
        :param event: QResizeEvent
        """

        super(LibrarySearchWidget, self).resizeEvent(event)

        self.setTextMargins(self.height(), 0, 0, 0)
        size = QSize(self.height(), self.height())
        self._icon_btn.setIconSize(size)
        self._icon_btn.setFixedSize(size)
        self._clear_btn.setIconSize(size)
        x = self.width() - self.height()
        self._clear_btn.setGeometry(x, 0, self.height(), self.height())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear()
        super(LibrarySearchWidget, self).keyPressEvent(event)

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library

    def settings(self):
        """
        Returns a dictionary of the current widget state
        :return: dict
        """

        settings = {
            'text': self.text(),
            'spaceOperator': self.space_operator()
        }

        return settings

    def set_settings(self, settings):
        """
        Restore the widget state from a settings dictonary
        :param settings: dict
        """

        text = settings.get('text', '')
        self.setText(text)
        space_operator = settings.get('spaceOperator')
        if space_operator:
            self.set_space_operator(space_operator)

    def space_operator(self):
        """
        Returns the space operator for the search widget
        :return: str
        """

        return self._space_operator

    def set_space_operator(self, space_operator):
        """
        Sets the space operator
        :param space_operator: str
        """

        self._space_operator = space_operator
        self.search()

    def update_clear_button(self):
        """
        Updates the clera button depending on the current text
        """

        text = self.text()
        if text:
            self._clear_btn.show()
        else:
            self._clear_btn.hide()

    def search(self):
        """
        Run the search query on the library
        """

        if self.library():
            self.library().add_query(self.query())
            self.library().search()
        else:
            qt.logger.info('No library found for the search widget')

        self.update_clear_button()
        self.searchChanged.emit()

    def query(self):
        """
        Returns the query used for the library
        :return: dict
        """

        text = str(self.text())
        filters = list()
        for filter_ in text.split(' '):
            if filter_.split():
                filters.append(('*', 'contains', filter_))
        unique_name = 'searchWidget' + str(id(self))

        return {'name': unique_name, 'operator': self.space_operator(), 'filters': filters}

    def set_icon(self, icon):
        """
        Sets the icon for the search widget
        :param icon: QIcon
        """

        self._icon_btn.setIcon(icon)

    def set_icon_color(self, color):
        """
        Sets the icon color for the search widget icon
        :param color: QColor
        """

        btn_icon = self._icon_btn.icon()
        btn_icon = icon.Icon(btn_icon)
        btn_icon.set_color(color)
        self._icon_btn.setIcon(btn_icon)

        clear_icon = self._clear_btn.icon()
        clear_icon = icon.Icon(clear_icon)
        clear_icon.set_color(color)
        self._clear_btn.setIcon(clear_icon)

    def update_icon_color(self):
        """
        Updates the icon colors to the current foreground role
        """

        clr = self.palette().color(self.foregroundRole())
        clr = color.Color.from_color(clr)
        self.set_icon_color(clr)

    def _on_icon_clicked(self):
        """
        Internal callback function that is triggered when the user clcks on the search icon
        """

        if not self.hasFocus():
            self.setFocus()

    def _on_clear_clicked(self):
        """
        Internal callback function that is triggered when the user clicks the cross icon
        """

        self.setText('')
        self.setFocus()

    def _on_text_changed(self):
        """
        Internal callback function that is triggered when the text changes
        """

        self.search()


class LibraryStatusWidget(statusbar.StatusWidget, object):
    DEFAULT_DISPLAY_TIME = 10000

    INFO_CSS = ''

    WARNING_CSS = """
        color: rgb(240, 240, 240);
        background-color: rgb(240, 170, 0);
    """

    ERROR_CSS = """
        color: rgb(240, 240, 240);
        background-color: rgb(220, 40, 40);
        selection-color: rgb(220, 40, 40);
        selection-background-color: rgb(240, 240, 240);
    """

    def __init__(self, *args):
        super(LibraryStatusWidget, self).__init__(*args)

        self.setFixedHeight(19)
        self.setMinimumWidth(5)

        self.main_layout.setContentsMargins(1, 0, 0, 0)

        self._progress_bar = progressbar.FrameProgressBar(self)
        self._progress_bar.hide()
        self.main_layout.addWidget(self._progress_bar)

    def show_info_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_info_message function
        Set an info message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        self.setStyleSheet('')
        super(LibraryStatusWidget, self).show_info_message(message, msecs)

    def show_warning_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_warning_message function
        Set a warning message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        if self.is_blocking():
            return

        self.setStyleSheet(self.WARNING_CSS)
        super(LibraryStatusWidget, self).show_warning_message(message, msecs)

    def show_error_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_error_message function
        Set an error message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        self.setStyleSheet(self.ERROR_CSS)
        super(LibraryStatusWidget, self).show_error_message(message, msecs)

    def progress_bar(self):
        """
        Returns the progress bar widget
        :return:  progressbar.ProgressBar
        """

        return self._progress_bar


class LibraryToolbarWidget(toolbar.ToolBar, object):

    def __init__(self, *args):
        super(LibraryToolbarWidget, self).__init__(*args)

        self._dpi = 1

    def dpi(self):
        """
        Returns the zoom multiplier
        :return: float
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Set the zoom multiplier
        :param dpi: float
        """

        self._dpi = dpi

    def expand_height(self):
        """
        Overrides base toolbar.Toolbar expand_height function
        Returns the height of menu bar when is expanded
        :return: int
        """

        return int(self._expanded_height * self.dpi())

    def collapse_height(self):
        """
        Overrides base toolbar.Toolbar collapse_height function
        Returns the height of widget when collapsed
        :return: int
        """

        return int(self._collapsed_height * self.dpi())


class LibrarySideBarWidgetItem(QTreeWidgetItem, object):
    def __init__(self, *args):
        super(LibrarySideBarWidgetItem, self).__init__(*args)

        self._path = ''
        self._bold = None
        self._icon_path = None
        self._icon_color = None
        self._text_color = None
        self._expanded_icon_path = None
        self._collapsed_icon_path = None

        self._settings = dict()

    def setSelected(self, select):
        """
        Overrides base LibrarySideBarWidget setSelected function
        :param select: bool
        """

        super(LibrarySideBarWidgetItem, self).setSelected(select)
        if select:
            self.set_expanded_parents(select)

    def path(self):
        """
        Returns item path
        :return: str
        """

        return self._path

    def set_path(self, path):
        """
        Sets the path for the item
        :param path: str
        """

        self._path = path

    def default_icon_path(self):
        """
        Returns the default icon path
        :return: str
        """

        return ''

    def expanded_icon_path(self):
        """
        Returns the icon path to be shown when expanded
        :return: str
        """

        return self._expanded_icon_path or tpDcc.ResourcesMgr().get('icons', 'black', 'open_folder')

    def collapsed_icon_path(self):
        """
        Returns the icon path to be shown when collapsed
        :return: str
        """

        return self._collapsed_icon_path or tpDcc.ResourcesMgr().get('icons', 'black', 'folder')

    def icon_path(self):
        """
        Returns the icon path for the item
        :return: str
        """

        return self._icon_path or self.default_icon_path()

    def set_icon_path(self, path):
        """
        Sets the icon path for the item
        :param path: str
        """

        self._icon_path = path
        self.update_icon()

    def default_icon_color(self):
        """
        Returns the default icon color
        :return: str
        """

        palette = self.treeWidget().palette()
        clr = palette.color(self.treeWidget().foregroundRole())
        clr = color.Color.from_color(clr).to_string()

        return str(clr)

    def icon_color(self):
        """
        Returns the icon color
        :return: variant, QColor or None
        """

        return self._icon_color or self.default_icon_color()

    def set_icon_color(self, icon_color):
        """
        Sets the icon color
        :param icon_color: variant, QColor or str
        """

        if isinstance(icon_color, QColor):
            icon_color = color.Color.from_color(icon_color)
        elif isinstance(icon_color, (str, unicode)):
            icon_color = color.Color.from_string(icon_color)

        self._icon_color = icon_color.to_string()
        self.update_icon()

    def textColor(self):
        """
        Returns the foreground color of the item
        :return: QColor
        """

        clr = self.foreground(0).color()
        return color.Color.from_color(clr)

    def setTextColor(self, text_color):
        """
        Sets the foreground color to the given color
        :param text_color: variant, QColor or str
        """

        if isinstance(text_color, QColor):
            text_color = color.Color.from_color(text_color)
        elif isinstance(text_color, (str, unicode)):
            text_color = color.Color.from_string(text_color)
        self._settings['textColor'] = text_color.to_string()
        brush = QBrush()
        brush.setColor(text_color)
        self.setForeground(0, brush)

    def bold(self):
        """
        Returns whether item text is bold or not
        :return: bool
        """

        return self.font(0).bold()

    def set_bold(self, flag):
        """
        Sets whether item text is bold or not
        :param flag: bool
        """

        if flag:
            self._settings['bold'] = flag

        font = self.font(0)
        font.setBold(flag)
        self.setFont(0, font)

    def update_icon(self):
        """
        Forces the icon to update
        """

        path = self.icon_path()
        if not path:
            if self.isExpanded():
                path = self.expanded_icon_path()
            else:
                path = self.collapsed_icon_path()

        clr = self.icon_color()
        px = pixmap.Pixmap(path)
        px.set_color(clr)

        self.setIcon(0, px)

    def url(self):
        """
        Returns the url path
        :return: QUrl
        """

        return QUrl(self.path())

    def parents(self):
        """
        Returns all item parents
        :return: list(LibrarySidebarWidgetItem)
        """

        parents = list()
        parent = self.parent()
        if parent:
            parents.append(parent)
            while parent.parent():
                parent = parent.parent()
                parents.append(parent)

        return parents

    def set_expanded_parents(self, expanded):
        """
        Sets all the parents of the item to the value of expanded
        :param expanded: bool
        """

        parents = self.parents()
        for parent in parents:
            parent.setExpanded(expanded)

    def update(self):
        """
        Updates item
        """

        self.update_icon()

    def settings(self):
        """
        Returns the current state of the item as a dictionary
        :return: dict
        """

        settings = dict()

        is_selected = self.isSelected()
        if is_selected:
            settings['selected'] = is_selected
        is_expanded = self.isExpanded()
        if is_expanded:
            settings['expanded'] = is_expanded
        icon_path = self.icon_path()
        if icon_path != self.default_icon_path():
            settings['iconPath'] = icon_path
        icon_color = self.icon_color()
        if icon_color != self.default_icon_color():
            settings['iconColor'] = icon_color
        bold = self._settings.get('bold')
        if bold:
            settings['bold'] = bold
        text_color = self._settings.get('textColor')
        if text_color:
            settings['textColor'] = text_color

        return settings

    def set_settings(self, settings):
        """
        Sets the current state of the item from a dictionary
        :param settings: dict
        """

        text = settings.get('text')
        if text:
            self.setText(0, text)
        icon_path = settings.get('iconPath')
        if icon_path:
            self.set_icon_path(icon_path)
        icon_color = settings.get('iconColor')
        if icon_color:
            self.set_icon_color(icon_color)
        is_selected = settings.get('selected')
        if is_selected:
            self.setSelected(is_selected)
        is_expanded = settings.get('expanded')
        if is_expanded and self.childCount() > 0:
            self.setExpanded(is_expanded)
        bold = settings.get('bold')
        if bold:
            self.set_bold(bold)
        text_color = settings.get('textColor')
        if text_color:
            self.setTextColor(text_color)


class LibrarySidebarWidget(QTreeWidget, object):

    itemRenamed = Signal(str, str)
    itemDropped = Signal(object)
    itemSelectionChanged = Signal()

    DEFAULT_SEPARATOR = '/'

    @classmethod
    def paths_to_dict(cls, paths, root='', separator=None):
        """
        Returns the given paths as a nested dict
        paths = ['/test/a', '/test/b']
        Result = {'test' : {'a':{}}, {'b':{}}}
        :param paths: list(str)
        :param root: str
        :param separator: str or None
        :return: dict
        """

        separator = separator or cls.DEFAULT_SEPARATOR
        results = OrderedDict()

        for path in paths:
            p = results
            # This is to add support for grouping by the given root path.
            if root and root in path:
                path = path.replace(root, "")
                p = p.setdefault(root, OrderedDict())
            keys = path.split(separator)[0:]
            for key in keys:
                if key:
                    p = p.setdefault(key, OrderedDict())

        return results

    @classmethod
    def find_root(cls, paths, separator=None):
        """
        Finds the common path for the given paths
        :param paths: list(str)
        :param separator: str
        :return: str
        """

        if not paths:
            return

        path = paths[0]
        result = None
        separator = separator or cls.DEFAULT_SEPARATOR
        tokens = path.split(separator)
        for i, token in enumerate(tokens):
            root = separator.join(tokens[:i + 1])
            match = True
            for path in paths:
                if not path.startswith(root + separator):
                    match = False
                    break
            if not match:
                break
            result = root

        return result

    def __init__(self, *args):
        super(LibrarySidebarWidget, self).__init__(*args)

        self._dpi = 1
        self._items = list()
        self._index = dict()
        self._locked = False
        self._library = None
        self._recursive = True
        self._options = {
            'field': 'path',
            'separator': '/',
            'recursive': True,
            'autoRootPath': True,
            'rootText': 'FOLDERS',
            'sortBy': None,
            'queries': [{'filters': [('type', 'is', 'Folder')]}]
        }

        self.set_dpi(1)

        self.setAcceptDrops(True)
        self.setHeaderHidden(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.itemExpanded.connect(self.update)
        self.itemCollapsed.connect(self.update)

    def update(self, *args):
        """
        Overrides base QTreeWidet update function
        :param args: list
        """

        for item in self.items():
            item.update()

    def selectionChanged(self, *args):
        """
        Overrides base QTreeWidget selectionChanged function
        :param args: list
        """

        self.search()

    def items(self):
        """
        Returns a list of all the items in the tree widget
        :return: list(QTreeWidgetItem)
        """

        items = self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive)
        return items

    def settings(self):
        """
        Returns a dictionary of the settings for this widget
        :return: dict
        """

        settings = dict()
        vertical_scrollbar = self.verticalScrollBar()
        horizontal_scrollbar = self.horizontalScrollBar()
        settings['verticalScrollBar'] = {'value': vertical_scrollbar.value()}
        settings['horizontalScrollBar'] = {'value': horizontal_scrollbar.value()}
        for item in self.items():
            item_settings = item.settings()
            if item_settings:
                settings[item.path()] = item.settings()

        return settings

    def set_settings(self, settings):
        """
        Sets the settings for this widget
        :param settings: dict
        """

        for path in sorted(settings.keys()):
            s = settings.get(path, None)
            self.set_path_settings(path, s)
        vertical_scrollbar_settings = settings.get('verticalScrollBar', dict())
        value = vertical_scrollbar_settings.get('value', None)
        if value:
            self.verticalScrollBar().setValue(value)
        horizontal_scrollbar_settings = settings.get('horizontalScrollBar', dict())
        value = horizontal_scrollbar_settings.get('value', None)
        if value:
            self.horizontalScrollBar().setValue(value)
        self.setIndentation(18 * self.dpi())

    def set_path_settings(self, path, settings):
        """
        Set paths settings
        :param path: list(str)
        :param settings: dict
        """

        item = self.item_from_path(path)
        if item and settings:
            item.set_settings(settings)

    def set_data(self, data, root='', split=None):
        """
        Sets the items to the given items
        :param data: list(str)
        :param root: str
        :param split: str
        """

        settings = self.settings()
        self.blockSignals(True)
        try:
            self.clear()
            if not root:
                root = self.find_root(data.keys(), self.separator())
            self.add_paths(data, root=root, split=split)
            self.set_settings(settings)
        except Exception as e:
            qt.logger.error('{} | {}'.format(e, traceback.format_exc()))
        finally:
            self.blockSignals(False)

    def add_paths(self, paths, root='', split=None):
        """
        Set the given items as a flat list
        :param paths: list(str)
        :param root: str or None
        :param split: str or None
        """

        data = self.paths_to_dict(paths, root=root, separator=split)
        self.create_items(data, split=split)
        if isinstance(paths, dict):
            self.set_settings(paths)

    def create_items(self, data, split=None):
        """
        Creates the items from the given data dict
        :param data: dict
        :param split: str or None
        """

        split = split or self.DEFAULT_SEPARATOR
        self._index = dict()
        for key in data:
            path = split.join([key])
            item = LibrarySideBarWidgetItem(self)
            item.setText(0, str(key))
            item.set_path(path)
            self._index[path] = item
            if self.root_text():
                item.setText(0, self.root_text())
                item.set_bold(True)
                item.set_icon_path('none')
                item.setExpanded(True)

            def _recursive(parent, children, split=None):
                for text, val in sorted(children.iteritems()):
                    p = parent.path()
                    p = split.join([p, text])
                    child = LibrarySideBarWidgetItem()
                    child.setText(0, str(text))
                    child.set_path(p)
                    parent.addChild(child)
                    self._index[p] = child
                    _recursive(child, val, split=split)

            _recursive(item, data[key], split=split)

        self.update()

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library
        self._library.dataChanged.connect(self._on_data_changed)
        self._on_data_changed()

    def dpi(self):
        """
        Returns the zoom multiplier
        :return: float
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Sets zoom multiplier
        :param dpi: float
        """

        size = 24 * dpi
        self.setIndentation(15 * dpi)
        self.setMinimumWidth(35 * dpi)
        self.setIconSize(QSize(size, size))
        self.setStyleSheet('height: {}'.format(size))

    def is_recursive(self):
        """
        Returns whether the recursive query is enabled or not
        :return: bool
        """

        return self._recursive

    def set_recursive(self, enable):
        """
        Sets whether recursive query is enabled or not
        :param enable: bool
        """

        self._recursive = enable
        self.search()

    def is_locked(self):
        """
        Returns whether widget items are read only or not
        :return: bool
        """

        return self._locked

    def set_locked(self, locked):
        """
        Sets whether widget items are read only or not
        :param locked: bool
        """

        self._locked = locked

    def separator(self):
        """
        Returns the separator used in the fields to seaprate level values
        :return: str
        """

        return self._options.get('separator', self.DEFAULT_SEPARATOR)

    def root_text(self):
        """
        Returns the root text
        :return: str
        """

        return self._options.get('rootText')

    def field(self):
        """
        Returns the field
        :return: str
        """

        return self._options.get('field', '')

    def sort_by(self):
        """
        Returns the sort by field
        :return: str
        """

        return self._options.get('sortBy', [self.field()])

    def select_item(self, item):
        """
        Selects given item
        :param item: QTreeWidgetItem
        """

        self.select_paths([item.path()])

    def selected_item(self):
        """
        Returns the current selected item
        :return: QTreeWidgetItem
        """

        path = self.selected_path()
        return self.item_from_path(path)

    def selected_path(self):
        """
        Returns the current selected path
        :return: str
        """
        paths = self.selected_paths()
        if paths:
            return paths[-1]

    def selected_paths(self):
        """
        Returns the paths that are selected
        :return: list(str)
        """

        paths = list()
        items = self.selectedItems()
        for item in items:
            path = item.path()
            paths.append(path)

        return paths

    def select_path(self, path):
        """
        Selects the given path
        :param path: str
        """

        self.select_paths([path])

    def select_paths(self, paths):
        """
        Select the items with the given paths
        :param paths: list(str)
        """

        paths = self._normalize_paths(paths)
        items = self.items()
        for item in items:
            if item.path() in paths:
                item.setSelected(True)
            else:
                item.setSelected(False)

    def select_url(self, url):
        """
        Select the item with the given url
        :param url: str
        """

        items = self.items()
        for item in items:
            if item.url() == url:
                item.setSelected(True)
            else:
                item.setSelected(False)

    def selected_urls(self):
        """
        Returns the urls for the selected items
        :return: list(str)
        """

        urls = list()
        items = self.selectedItems()
        for item in items:
            urls.append(item.url())

        return urls

    def item_from_url(self, url):
        """
        Returns the item for the given URL
        :param url: QUrl
        :return: QTreeWidgetItem
        """

        for item in self.items():
            if url == item.url():
                return item

    def item_from_path(self, path):
        """
        Returns the item for the given path
        :param path: str
        :return: QTreeWidgetItem
        """

        return self._index.get(path)

    def expanded_items(self):
        """
        Returns all the expanded items
        :return: list(QTreeWidgetItem)
        """

        for item in self.items():
            if self.isItemExpanded(item):
                yield item

    def expanded_paths(self):
        """
        Returns all the expanded paths
        :return: list(QUrl)
        """

        for item in self.expanded_items():
            yield item.url()

    def set_expanded_paths(self, paths):
        """
        Stes the given paths as expanded
        :param paths: list(str)
        """

        for item in self.items():
            if item.url() in paths:
                item.setExpanded(True)

    def search(self):
        """
        Runs library search
        """

        if self.library():
            self.library().add_query(self.query())
            self.library().search()
        else:
            qt.logger.info('No library found for the sidebar widget')

    def query(self):
        """
        Returns the query for the sidebar widget
        :return: dict
        """

        filters = list()

        for path in self.selected_paths():
            if self.is_recursive():
                filter_ = ('folder', 'startswith', path + '/')
                filters.append(filter_)
            filter_ = ('folder', 'is', path)
            filters.append(filter_)
        unique_name = 'sidebar_widget_' + str(id(self))
        return {'name': unique_name, 'operator': 'or', 'filters': filters}

    def clear(self):
        """
        Clears all the items from the tree widget
        """

        self._items = list()
        self._index = dict()
        super(LibrarySidebarWidget, self).clear()

    def _normalize_paths(self, paths):
        """
        Normalizes given paths
        :param paths: list(str)
        :return: list(str)
        """

        return [path.replace('\\', '/') for path in paths]

    def _on_data_changed(self):
        """
        Internal callback function that is triggered when the library data changes
        """

        pass


class SortByMenu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(SortByMenu, self).__init__(*args, **kwargs)

        self._library = None

    def show(self, point=None):
        """
        Overrides base QMenu show function
        :param point: QPoint
        """

        self.clear()

        sort_by = self.library().sort_by()
        if sort_by:
            current_field = self.library().sort_by()[0].split(':')[0]
            current_order = 'dsc' if 'dsc' in self.library().sort_by()[0] else 'asc'
        else:
            current_field = ''
            current_order = ''

        separator_action = action.SeparatorAction('Sort By', self)
        self.addAction(separator_action)

        fields = self.library().SortFields
        for field in fields:
            field_action = self.addAction(field.title())
            field_action.setCheckable(True)
            field_action.setChecked(bool(current_field == field))
            callback = partial(self.set_sort_by, field, current_order)
            field_action.triggered.connect(callback)

        separator_action = action.SeparatorAction('Sort Order', self)
        self.addAction(separator_action)

        ascending_action = self.addAction('Ascending')
        ascending_action.setCheckable(True)
        ascending_action.setChecked(bool(current_order == 'asc'))
        callback = partial(self.set_sort_by, current_field, 'asc')
        ascending_action.triggered.connect(callback)

        descending_action = self.addAction('Descending')
        descending_action.setCheckable(True)
        descending_action.setChecked(bool(current_order == 'dsc'))
        callback = partial(self.set_sort_by, current_field, 'dsc')
        descending_action.triggered.connect(callback)

        if not point:
            point = QCursor.pos()

        self.exec_(point)

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library

    def set_sort_by(self, sort_name, sort_order):
        """
        Sets the sort by value for the library
        :param sort_name: str
        :param sort_order: str
        """

        if sort_name == 'Custom Order':
            sort_order = 'asc'

        value = sort_name + ':' + sort_order
        self.library().set_sort_by([value])
        self.library().search()


class GroupByMenu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(GroupByMenu, self).__init__(*args, **kwargs)

        self._library = None

    def show(self, point=None):
        """
        Overrides base QMenu show function
        :param point: QPoint
        """

        self.clear()

        group_by = self.library().group_by()
        if group_by:
            current_field = group_by[0].split(':')[0]
            current_order = 'dsc' if 'dsc' in group_by[0]else 'asc'
        else:
            current_field = ''
            current_order = ''

        separator_action = action.SeparatorAction('Group By', self)
        self.addAction(separator_action)

        none_action = self.addAction('None')
        none_action.setCheckable(True)
        callback = partial(self.set_group_by, None, None)
        none_action.triggered.connect(callback)

        fields = self.library().GroupFields
        for field in fields:
            field_action = self.addAction(field.title())
            field_action.setCheckable(True)
            field_action.setChecked(bool(current_field == field))
            callback = partial(self.set_group_by, field, current_order)
            field_action.triggered.connect(callback)

        separator_action = action.SeparatorAction('Group Order', self)
        self.addAction(separator_action)

        ascending_action = self.addAction('Ascending')
        ascending_action.setCheckable(True)
        ascending_action.setChecked(bool(current_order == 'asc'))
        callback = partial(self.set_group_by, current_field, 'asc')
        ascending_action.triggered.connect(callback)

        descending_action = self.addAction('Descending')
        descending_action.setCheckable(True)
        descending_action.setChecked(bool(current_order == 'dsc'))
        callback = partial(self.set_group_by, current_field, 'dsc')
        descending_action.triggered.connect(callback)

        if not point:
            point = QCursor.pos()

        self.exec_(point)

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library

    def set_group_by(self, group_name, group_order):
        """
        Sets the group by value for the library
        :param group_name: str
        :param group_order: str
        """

        if group_name:
            value = [group_name + ':' + group_order]
        else:
            value = None

        self.library().set_group_by(value)
        self.library().search()


class FilterByMenu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(FilterByMenu, self).__init__(*args, **kwargs)

        self._facets = list()
        self._library = None
        self._options = {'field': 'type'}
        self._settings = dict()

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library
        library.searchStarted.connect(self._on_search_init)

    def _on_search_init(self):
        pass

    def settings(self):
        """
        Returns the settings for the filter menu
        :return: dict
        """

        return self._settings

    def set_settings(self, settings):
        """
        Set the settings for the filter menu
        :param settings: dict
        """

        self._settings = settings

    def name(self):
        """
        Returns the name of the fulter used by the library
        """

        return self._options.get('field') + 'FilterMenu'

    def set_all_enabled(self, enabled):
        """
        Set all the filters enabled
        :param enabled: bool
        """

        for facet in self._facets:
            self._settings[facet.get('name')] = enabled

    def is_show_all_enabled(self):
        """
        Returns whether all current filters are enabled or not
        :return: bool
        """

        for facet in self._facets:
            if not self._settings.get(facet.get('name'), True):
                return False

        return True

    def is_active(self):
        """
        Returns whether are any filters currently active using the settings
        :return: bool
        """

        settings = self.settings()
        for name in settings:
            if not settings.get(name):
                return True

        return False

    def set_options(self, options):
        """
        Sets the options to be used by the filters menu
        :param options: dict
        """

        self._options = options

    def show(self, point=None):
        """
        Shows the menu options
        :param point: variant, QPoint or None
        """

        self.clear()

        field = self._options.get('field')
        queries = self.library().queries(exclude=self.name())
        self._facets = self.library().distinct(field, queries=queries)
        separator_action = action.SeparatorAction('Show {}'.format(field.title()), self)
        self.addAction(separator_action)
        label_action = action.LabelAction('Show All', self)
        self.addAction(label_action)

        label_action.setEnabled(not self.is_show_all_enabled())
        callback = partial(self._on_show_all_clicked)
        label_action.triggered.connect(callback)

        self.addSeparator()

        for facet in self._facets:
            name = facet.get('name', '')
            checked = self.settings().get(name, True)
            filter_by_action = FilterByAction(self)
            filter_by_action.set_facet(facet)
            filter_by_action.setChecked(checked)
            self.addAction(filter_by_action)
            callback = partial(self._on_action_checked, name, not checked)
            filter_by_action.triggered.connect(callback)

        point = point or QCursor.pos()

        self.exec_(point)

    def _on_search_init(self):
        """
        Internal callback function that is triggered before each search to update the filter menu query
        """

        filters = list()
        settings = self.settings()
        field = self._options.get('field')
        for name in settings:
            checked = settings.get(name, True)
            if not checked:
                filters.append((field, 'not', name))

        query = {
            'name': self.name(),
            'operator': 'and',
            'filters': filters
        }

        self.library().add_query(query)

    def _on_action_checked(self, name, checked):
        """
        Internal callback function triggered when an action has been clicked
        :param name: str
        :param checked: bool
        """

        if qtutils.is_control_modifier():
            self.set_all_enabled(False)
            self._settings[name] = True
        else:
            self._settings[name] = checked

        self.library().search()

    def _on_show_all_clicked(self):
        """
        Internal callback function that is triggered when the user clicks the show all action
        """

        self.set_all_enabled(True)
        self.library().search()


class FilterByAction(QWidgetAction, object):
    def __init__(self, parent=None):
        super(FilterByAction, self).__init__(parent)

        self._facet = None
        self._checked = False

    def setChecked(self, checked):
        """
        Overrides base QWidgetAction setChecked function
        :param checked: bool
        """

        self._checked = checked

    def set_facet(self, facet):
        """
        Sets action facet
        :param facet:
        """

        self._facet = facet

    def createWidget(self, menu):
        """
        Overrides base QWidgetAction createWidget function
        :param menu: QMenu
        :return: QWidget
        """

        widget = QFrame(self.parent())
        widget.setObjectName('filterByAction')
        facet = self._facet
        name = facet.get('name', '')
        count = str(facet.get('count', 0))
        title = name.replace('.', '').title()
        label = QCheckBox(widget)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        label.setText(title)
        label.installEventFilter(self)
        label.setChecked(self._checked)
        label2 = QLabel(widget)
        label2.setObjectName('actionCounter')
        label2.setText(count)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(label, stretch=1)
        layout.addWidget(label2)
        widget.setLayout(layout)

        label.toggled.connect(self._on_triggered)

        return widget

    def _on_triggered(self, checked=None):
        """
        Triggered when teh checkbox value has changed
        :param checked: bool
        """

        self.triggered.emit()
        self.parent().close()
