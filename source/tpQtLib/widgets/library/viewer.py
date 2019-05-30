#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains library viewer widget implementation
"""

from __future__ import print_function, division, absolute_import

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *

from tpQtLib.core import base
from tpQtLib.widgets import toast
from tpQtLib.widgets.library import consts, treewidget, listview, items


class LibraryViewerDelegate(QStyledItemDelegate, object):
    """
    Class that defines visual style in LibraryViewer of LibraryItems
    """

    def __init__(self):
        super(LibraryViewerDelegate, self).__init__()

        self._viewer = None

    """
    ##########################################################################################
    OVERRIDES
    ##########################################################################################
    """

    def sizeHint(self, option, index):
        """
        Overrides base QStyledItemDelegate sizeHint function
        Return the size for the given id¡ndex
        :param option: QStylOptionViewItem
        :param index: QModelIndex
        :return: QSize
        """

        item = self.viewr().item_from_index(index)
        if isinstance(item, items.LibraryGroupItem):
            return item.sizeHint()

        return self.viewer().item_size_hint(index)

    def paint(self, painter, option, index):
        """
        Overrides base QStyledItemDelegate paint function
        Paint performs low-level painting for the given model index
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: QModelIndex
        """

        item = self.viewer().item_from_index(index)
        item.paint(painter, option, index)

    """
    ##########################################################################################
    VIEWER
    ##########################################################################################
    """

    def viewer(self):
        """
        Returns LibraryViewer object associated to this delegate
        :return: LibraryViewer
        """

        return self._viewer

    def set_viewer(self, viewer):
        """
        Set LibraryViewer associated to this delegate
        :param viewer: LibraryViewer
        """

        self._viewer = viewer


class LibraryViewer(base.BaseWidget, object):
    """
    Class that implements library viewer widget
    """

    IconMode = consts.DEFAULT_ICON_MODE
    TableMode = consts.DEFAULT_TABLE_MODE

    DEFAULT_PADDING = consts.VIEWER_DEFAULT_PADDING
    DEFAULT_ZOOM_AMOUNT = consts.VIEWER_DEFAULT_ZOOM_AMOUNT
    DEFAULT_TEXT_HEIGHT = consts.VIEWER_DEFAULT_TEXT_HEIGHT
    DEFAULT_WHEEL_SCROLL_STEP = consts.VIEWER_DEFAULT_WHEEL_SCROLL_STEP
    DEFAULT_MIN_SPACING = consts.VIEWER_DEFAULT_MIN_SPACING
    DEFAULT_MAX_SPACING = consts.VIEWER_DEFAULT_MAX_SPACING
    DEFAULT_MIN_LIST_SIZE = consts.VIEWER_DEFAULT_MIN_LIST_SIZE
    DEFAULT_MIN_ICON_SIZE = consts.VIEWER_DEFAULT_MIN_ICON_SIZE

    DEFAULT_TEXT_COLOR = consts.VIEWER_DEFAULT_TEXT_COLOR
    DEFAULT_SELECTED_TEXT_COLOR = consts.VIEWER_DEFAULT_SELECTED_TEXT_COLOR
    DEFAULT_BACKGROUND_COLOR = consts.VIEWER_DEFAULT_BACKGROUND_COLOR
    DEFAULT_BACKGORUND_HOVER_COLOR = consts.VIEWER_DEFAULT_BACKGROUND_HOVER_COLOR
    DEFAULT_BACKGROUND_SELECTED_COLOR = consts.VIEWER_DEFAULT_BACKGROUND_SELECTED_COLOR

    TREE_WIDGET_CLASS = treewidget.LibraryTreeWidget
    LIST_VIEW_CLASS = listview.LibraryListView
    DELEGATE_CLASS = LibraryViewerDelegate

    itemClicked = Signal(object)
    itemDoubleClicked = Signal(object)
    zoomChanged = Signal(object)
    spacingChanged = Signal(object)
    groupClicked = Signal(object)

    def __init__(self, parent=None):

        self._dpi = 1
        self._padding = self.DEFAULT_PADDING

        self._library = None
        self._tree_widget = None
        self._list_widget = None
        self._delegate = None
        self._is_item_text_visible = True
        self._toast_enabled = True

        self._zoom_amount = self.DEFAULT_ZOOM_AMOUNT
        self._icon_size = QSize(self._zoom_amount, self._zoom_amount)
        self._item_size_hint = QSize(self._zoom_amount, self._zoom_amount)

        self._text_color = self.DEFAULT_TEXT_COLOR
        self._text_selected_color = self.DEFAULT_SELECTED_TEXT_COLOR
        self._background_color = self.DEFAULT_BACKGROUND_COLOR
        self._background_hover_color = self.DEFAULT_BACKGORUND_HOVER_COLOR
        self._background_selected_color = self.DEFAULT_BACKGROUND_SELECTED_COLOR

        super(LibraryViewer, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        return main_layout

    def ui(self):
        super(LibraryViewer, self).ui()

        self._tree_widget = self.TREE_WIDGET_CLASS(self)

        self._list_view = self.LIST_VIEW_CLASS(self)
        self._list_view.set_tree_widget(self._tree_widget)

        self._delegate = self.DELEGATE_CLASS()
        self._delegate.set_viewer(self)
        self._list_view.setItemDelegate(self._delegate)
        self._tree_widget.setItemDelegate(self._delegate)

        self._toast_widget = toast.ToastWidget(self)
        self._toast_widget.hide()

        self.main_layout.addWidget(self._tree_widget)
        self.main_layout.addWidget(self._list_view)

        self.itemMoved = self._list_view.itemMoved
        self.itemDropped = self._list_view.itemDropped
        self.itemSelectionChanged = self._tree_widget.itemSelectionChanged

    def setup_signals(self):
        header = self.tree_widget().header()
        header.sortIndicatorChanged.connect(self._on_sort_indicator_changed)
        self._list_view.itemClicked.connect(self._on_item_clicked)
        self._list_view.itemDoubleClicked.connect(self._on_item_double_clicked)

    def wheelEvent(self, event):
        """
        Overrides base wheelEvent function
        Triggered on any wheel events for the current widget
        :param event: QWheelEvent
        """

        modifier = QApplication.keyboardModifiers()
        valid_modifiers = (Qt.AltModifier, Qt.ControlModifier)
        if modifier in valid_modifiers:
            num_degrees = event.delta() / 8
            num_steps = num_degrees / 15
            delta = (num_steps * self.wheel_scroll_step())
            value = self.zoom_amount() + delta
            self.set_zoom_amount(value)

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

    def library(self):
        """
        Returns the library attached to the viewer
        :return: variant
        """

        return self._library

    def set_library(self, library):
        """
        Sets the data that will be showed in viewer
        :param library:
        """

        self._library = library
        self.set_column_labels(library.Fields)
        library.searchFinished.connect(self._on_update_items)

    def is_icon_view(self):
        """
        Returns whether widget is in icon mode or not
        :return: bool
        """

        return not self._list_view.isHidden()

    def is_table_view(self):
        """
        Returns whether widget is in list mode or not
        :return: bool
        """

        return not self._tree_widget.isHidden()

    def set_view_mode(self, mode):
        """
        Sets the view mode for this widget
        :param mode: str
        """

        if mode == self.IconMode:
            self.set_zoom_amount(self.DEFAULT_MIN_ICON_SIZE)
        elif mode == self.TableMode:
            self.set_zoom_amount(self.DEFAULT_MIN_ICON_SIZE)

    def set_list_mode(self):
        """
        Sets the tree widget visible
        """

        self._list_view.hide()
        self._tree_widget.show()
        self._tree_widget.setFocus()

    def set_icon_mode(self):
        """
        Sets the list view visible
        """

        self._tree_widget.hide()
        self._list_view.show()
        self._list_view.setFocus()

    def zoom_amount(self):
        """
        Returns the zoom amount for the widget
        :return: int
        """

        return self._zoom_amount

    def set_zoom_amount(self, value):
        """
        Sets the zoom amount for the widget
        :param value: int
        """

        if value < self.DEFAULT_MIN_LIST_SIZE:
            value = self.DEFAULT_MIN_LIST_SIZE

        self._zoom_amount = value
        size = QSize(value * self.dpi(), value * self.dpi())
        self.set_icon_size(size)
        if value >= self.DEFAULT_MIN_LIST_SIZE:
            self._set_view_mode(self.IconMode)
        else:
            self._set_view_mode(self.TableMode)
        column_width = value * self.dpi() + self.item_text_height()
        self._tree_widget.setIndentation(0)
        self._tree_widget.setColumnWidth(0, column_width)
        self.scroll_to_selected_item()
        self.show_toast_message('Size: {}%'.format(value))

    def vertical_scrollbar(self):
        """
        Returns the active vertical scroll bar
        :return: QScrollBar
        """

        if self.is_table_view():
            return self.tree_widget().verticalScrollBar()
        else:
            return self.list_view().verticalScrollBar()

    def visual_item_rect(self, item):
        """
        Returns the visual rect for the item
        :param item: LibraryItem
        :return: QRect
        """

        if self.is_table_view():
            visual_rect = self.tree_widget().visual_item_rect(item)
        else:
            index = self.tree_widget().index_from_item(item)
            visual_rect = self.list_view().visualRect(index)

        return visual_rect

    def is_item_visible(self, item):
        """
        Returns whether given item is visible or not
        :param item: LibraryItem
        :return: bool
        """

        height = self.height()
        item_rect = self.visual_item_rect(item)
        scroll_bar_y = self.vertical_scrollbar().value()
        y = (scroll_bar_y - item_rect.y()) + height

        return scroll_bar_y < y < scroll_bar_y + height

    def scroll_to_item(self, item):
        """
        Ensures the given item is visible
        :param item: LibraryItem
        """

        position = QAbstractItemView.PositionAtCenter
        if self.is_table_view():
            self.tree_widget().scroll_to_item(item, position)
        elif self.is_icon_view():
            self.list_view().scroll_to_item(item, position)

    def scroll_to_selected_item(self):
        """
        Ensures that selected item is visible
        """

        item = self.selected_item()
        if item:
            self.scroll_to_item(item)

    def item_at(self, pos):
        """
        Returns the current item at the given position
        :param pos: QPoint
        :return: LibraryItem
        """

        if self.is_icon_view():
            return self.list_view().item_at(pos)
        else:
            return self.tree_widget().item_at(pos)

    def insert_items(self, items, item_at=None):
        """
        Inserts the given items at the given position
        :param items: list(LibraryItem)
        :param item_at: LibraryItem
        """

        self.add_items(items)
        self.move_items(items, item_at=item_at)
        self.tree_widget().set_items_selected(items)

    def create_group_item(self, text, children=None):
        """
        Internal function that creates a new item for the given text and children
        :param text: str
        :param children: list(LibraryItem)
        """

        group_item = items.LibraryGroupItem()
        group_item.set_name(text)
        group_item.set_stretch_to_widget(self)
        group_item.set_children(children)

        return group_item

    def refresh(self):
        """
        Refreshes the item size
        """

        self.refresh_size()

    def refresh_size(self):
        """
        Refreshes the size of the items
        """

        self.set_zoom_amount(self.zoom_amount() + 1)
        self.set_zoom_amount(self.zoom_amount() - 1)
        self.repaint()

    def toggle_text_visible(self):
        """
        Toggle the item text visibility
        """

        if self.is_item_text_visible():
            self.set_item_text_visible(False)
        else:
            self.setItemTextVisible(True)

    def is_item_text_visible(self):
        """
        Returns whether item text is visible or not
        :return: bool
        """

        if self.is_icon_view():
            return self._is_item_text_visible
        else:
            return True

    def item_text_height(self):
        """
        Returns the height of the item text
        :return: int
        """

        return self.DEFAULT_TEXT_HEIGHT * self.dpi()

    def item_delegate(self):
        """
        Returns the item delegate for the views
        :return: LibraryViewerDelegate
        """

        return self._delegate

    def set_item_text_visible(self, flag):
        """
        Sets the visibility of the item text
        :param flag: bool
        """

        self._is_item_text_visible = flag
        self.refresh_size()

    def column_labels_from_items(self):
        """
        Returns the column labels for all the items
        :return: list(str)
        """

        seq = list()
        for item in self.items():
            seq.extend(item._text_column_order)
        seen = set()

        return [x for x in seq if x not in seen and not seen.add(x)]

    def refresh_columns(self):
        """
        Refresh columns labels
        """

        self.set_column_labels(self.column_labels_from_items())

    def padding(self):
        """
        Returns the item padding
        :return: int
        """

        return self._padding

    def set_padding(self, value):
        """
        Sets the item padding
        :param value: int
        """

        if value % 2 == 0:
            self._padding = value
        else:
            self._padding = value + 1
        self.repaint()
        self.show_toast_message('Border: {}'.format(value))

    def item_size_hint(self):
        """
        Returns the item size hint
        :return: QSize
        """

        return self._item_size_hint

    def icon_size(self):
        """
        Returns the icon size for the views
        :return: QSize
        """

        return self._icon_size

    def set_icon_size(self, size):
        """
        Sets the icon size for the views
        :param size: QSize
        """

        self._icon_size = size
        if self.is_item_text_visible():
            w = size.width()
            h = size.width() + self.item_text_height()
            self._item_size_hint = QSize(w, h)
        else:
            self._item_size_hint = size

        self.list_view().setIconSize(size)
        self.tree_widget().setIconSize(size)

    def wheel_scroll_step(self):
        """
        Returns the wheel scroll setp amount
        :return: int
        """

        return self.DEFAULT_WHEEL_SCROLL_STEP

    def _set_view_mode(self, mode):
        """
        Internal function that sets the view mode ro this widget
        :param mode: str
        :return: str
        """

        if mode == self.IconMode:
            self.set_icon_mode()
        elif mode == self.TableMode:
            self.set_list_mode()

    """
    ##########################################################################################
    DPI
    ##########################################################################################
    """

    def dpi(self):
        """
        Returns zoom multiplier
        :return: int
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Sets the zoom multiplier
        :param dpi: int
        """

        self._dpi = dpi
        self.refresh_size()

    """
    ##########################################################################################
    TOAST WIDGET
    ##########################################################################################
    """

    def toast_enabled(self):
        """
        Returns whether toast message widget is enabled or not
        :return: bool
        """

        return self._toast_enabled

    def set_toast_enabled(self, flag):
        """
        Sets whether toast widget is enabled or not
        :param flag: bool
        """

        self._toast_enabled = flag

    def show_toast_message(self, text, duration=300):
        """
        Shows a toast with the given text for the given duration
        :param text: str
        :param duration: None or int
        """

        if self.toast_enabled():
            self._toast_widget.set_duration(duration)
            self._toast_widget.setText(text)
            self._toast_widget.show()

    """
    ##########################################################################################
    TREE WIDGET
    ##########################################################################################
    """

    def tree_widget(self):
        """
        Returns the list view that contains the items
        :return: TreeWidget
        """

        return self._tree_widget

    def column_from_label(self, *args):
        """
        Returns column from given label text
        :return: int
        """

        return self.tree_widget().column_from_label(*args)

    def set_column_hidden(self, column, hidden):
        """
        Hides/Shows specific column in tree widget
        :param column: int
        :param hidden: bool
        """

        self.tree_widget().setColumnHidden(column, hidden)

    def set_column_labels(self, labels):
        """
        Set the columns for the viewer
        :param labels: list(str)
        """

        labels_set = set()
        set_add = labels_set.add
        labels = [x for x in labels if x.strip() and not (x in labels_set or set_add(x))]
        self.tree_widget().setHeaderLabels(labels)

    def index_from_item(self, item):
        """
        Returns the QModelIndex associated with the given item
        :param item: LibraryItem
        :return: QModelIndex
        """

        return self._tree_widget.index_from_item(item)

    def items(self):
        """
        Returns all the items in the tree widget
        :return: list(Item)
        """

        return self._tree_widget.items()

    def item_from_index(self, index):
        """
        Returns a pointer to the QTreeWidgetItem associated with the given index
        :param index: QModelIndex
        :return: QTreeWidgetItem
        """

        return self.tree_widget().itemFromIndex(index)

    def text_from_items(self, *args, **kwargs):
        """
        Returns all data for the given items and given column
        :return: list(str)
        """

        return self.tree_widget().text_from_items(*args, **kwargs)

    def text_from_column(self, *args, **kwargs):
        """
        Returns all data for the given column
        :return: list(str)
        """

        return self.tree_widget().text_from_column(*args, **kwargs)

    def add_item(self, item):
        """
        Add the item to the tree widget
        :param item: LibraryItem
        """

        self.add_items([item])

    def add_items(self, items):
        """
        Add the given items to the items widget
        :param items: list(LibraryItem)
        """

        self._tree_widget.addTopLevelItems(items)

    def selected_item(self):
        """
        Returns the last non-hidden selected item
        :return: LibraryItem
        """

        return self._tree_widget.selected_item()

    def selected_items(self):
        """
        Returns a list with all selected non-hiden items
        :return: list(QTreeWidgetItem)
        """

        return self._tree_widget.selectedItems()

    def clear_selection(self):
        """
        Cleras the user selection
        """

        self._tree_widget.clearSelection()

    def selection_model(self):
        """
        Returns the current selection model
        :return: QItemSelectionModel
        """

        return self._tree_widget.selectionModel()

    def model(self):
        """
        Returns the model the viewer is representing
        :return: QAbstractItemModel
        """

        return self._tree_widget.model()

    def update_items(self):
        """
        Sets the items to the viewer
        """

        selected_items = self.selected_items()
        self.clear_selection()

        results = self.library().grouped_results()

        items = list()

        for group in results:
            if group != 'None':
                group_item = self.create_group_item(group)
                items.append(group_item)
            items.extend(results[group])

        self.tree_widget().set_items(items)

        if selected_items:
            self.select_items(selected_items)
            self.scroll_to_selected_item()

    def clear(self):
        """
        Clear all elements in tree widget
        """

        self.tree_widget().clear()

    def _on_update_items(self):
        self.update_items()

    """
    ##########################################################################################
    LIST WIDGET
    ##########################################################################################
    """

    def list_view(self):
        """
        Returns the list view that contains the items
        :return: LibraryListView
        """

        return self._list_view

    def set_locked(self, value):
        """
        Disables drag and drop
        :param value: bool
        """

        self.list_view().setDragEnabled(not value)
        self.list_view().setDropEnabled(not value)

    def spacing(self):
        """
        Returns the spacing between the items
        :return: int
        """

        return self.list_view().spacing()

    def set_spacing(self, spacing):
        """
        Set the spacing between the items
        :param spacing: int
        """

        self.list_view().setSpacing(spacing)
        self.scroll_to_selected_item()
        self.show_toast_message('Spacing: {}'.format(spacing))

    def move_items(self, items, item_at=None):
        """
        Moves the given items to the given position
        :param items: list(LibraryItem)
        :param item_at: LibraryItem
        """

        self.list_view().move_items(items, item_at=item_at)

    """
    ##########################################################################################
    CALLBACKS
    ##########################################################################################
    """

    def _on_sort_indicator_changed(self):
        """
        Internal callback function that is called when sort indicator changes
        """

        pass

    def _on_item_clicked(self, item):
        """
        Internal callback function that is called when an item has been clicked
        :param item: LibraryItem
        """

        if isinstance(item, items.LibraryGroupItem):
            self.groupClicked.emit(item)
        else:
            self.itemClicked.emit(item)

    def _on_item_double_clicked(self, item):
        """
        Internal callback function that is called when an item has been double clicked
        :param item: LibraryItem
        """

        self.itemDoubleClicked.emit(item)
