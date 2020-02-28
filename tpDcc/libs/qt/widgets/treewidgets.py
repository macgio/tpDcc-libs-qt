#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt tree widgets
"""

from __future__ import print_function, division, absolute_import

import string

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs import qt
from tpDcc.libs.python import path, fileio, folder
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import buttons, search


class TreeWidget(QTreeWidget, object):

    ITEM_WIDGET = QTreeWidgetItem
    ITEM_WIDGET_SIZE = None

    SelectionChanged = Signal()

    def __init__(self, parent=None):
        super(TreeWidget, self).__init__(parent)

        self._auto_add_sub_items = True
        self._title_text_index = 0
        self._text_edit = True
        self._edit_state = None
        self._current_name = None
        self._old_name = None
        self._current_item = None
        self._last_item = None
        self._drop_indicator_rect = QRect()

        self.setIndentation(25)
        self.setExpandsOnDoubleClick(False)

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            self.setAlternatingRowColors(tp.Dcc.get_version() < 2016)

        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        if not tp.is_maya() and not not tp.is_nuke():
            palette = QPalette()
            palette.setColor(palette.Highlight, Qt.gray)
            self.setPalette(palette)

        self.itemCollapsed.connect(self._on_item_collapsed)
        self.itemActivated.connect(self._on_item_activated)
        self.itemChanged.connect(self._on_item_changed)
        self.itemSelectionChanged.connect(self._on_item_selection_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemExpanded.connect(self._on_item_expanded)

    @property
    def current_item(self):
        return self._current_item

    @property
    def current_name(self):
        return self._current_name

    @property
    def edit_state(self):
        return self._edit_state

    @edit_state.setter
    def edit_state(self, flag):
        self._edit_state = flag

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        self.drawTree(painter, event.region())
        self._paint_drop_indicator(painter)

    def mousePressEvent(self, event):
        super(TreeWidget, self).mousePressEvent(event)

        item = self.itemAt(event.pos())
        if not item:
            self._clear_selection()

    def mouseDoubleClickEvent(self, event):
        position = event.pos()
        index = self.indexAt(position)
        self.doubleClicked.emit(index)

    def dragMoveEvent(self, event):
        item = self.itemAt(event.pos())

        if item:
            index = self.indexFromItem(item)
            rect = self.visualRect(index)
            rect_left = self.visualRect(index.sibling(index.row(), 0))
            rect_right = self.visualRect(index.sibling(index.row(), self.header().logicalIndex(self.columnCount() - 1)))
            self._drop_indicator_position = self.position(event.pos(), rect, index)
            if self._drop_indicator_position == self.AboveItem:
                self._drop_indicator_rect = QRect(
                    rect_left.left(), rect_left.top(), rect_right.right() - rect_left.left(), 0)
                event.accept()
            elif self._drop_indicator_position == self.BelowItem:
                self._drop_indicator_rect = QRect(
                    rect_left.left(), rect_left.bottom(), rect_right.right() - rect_left.left(), 0)
                event.accept()
            elif self._drop_indicator_position == self.OnItem:
                self._drop_indicator_rect = QRect(
                    rect_left.left(), rect_left.top(), rect_right.right() - rect_left.left(), rect.height())
                event.accept()
            else:
                self._drop_indicator_rect = QRect()

            self.model().setData(index, self._drop_indicator_position, Qt.UserRole)

        self.viewport().update()

        super(TreeWidget, self).dragMoveEvent(event)

    def addTopLevelItem(self, item):
        super(TreeWidget, self).addTopLevelItem(item)

        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
            else:
                self.setItemWidget(item, 0, item.widget)

    def insertTopLevelItem(self, index, item):
        super(TreeWidget, self).insertTopLevelItem(index, item)

        if hasattr(item, 'widget'):
            if hasattr(item, 'column'):
                self.setItemWidget(item, item.column, item.widget)
            else:
                self.setItemWidget(item, 0, item.widget)

    def position(self, pos, rect, index):
        """
        Function that returns whether the cursor is over, below or on an item
        :param pos: QPos
        :param rect: QRect
        :param rect: QModelIndex
        :return: QAbstractItemView.DropIndicatorPosition
        """

        r = QAbstractItemView.OnViewport

        # NOTE: margin * 2 MUST be smaller than row height, otherwise drop OnItem rect will not show
        margin = 5

        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem
        elif pos.y() - rect.top() > margin and rect.bottom() - pos.y() > margin:
            r = QAbstractItemView.OnItem

        return r

    def unhide_items(self):
        """
        Unhide all tree items
        """

        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self.setItemHidden(item, False)

    def filter_names(self, filter_text):
        """
        Hides all tree items with the given text
        :param filter_text: str, text used to filter tree items
        """

        self.unhide_items()

        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            text = str(item.text(self._title_text_index))
            filter_text = str(filter_text)

            # If the filter text is not found on the item text, we hide the item
            if text.find(filter_text) == -1:
                self.setItemHidden(item, True)

    def get_tree_item_name(self, tree_item):
        """
        Returns a list with all the column names of the given QTreeWidgetItem
        :param tree_item: QTreeWidgetItem, item we want to retrive name of
        :return: list<str>
        """

        try:
            # When selecting an item in the tree and refreshing a C++ wrapped will raise
            count = QTreeWidgetItem.columnCount(tree_item)
        except Exception:
            count = 0

        name = list()
        for i in range(count):
            name.append(str(tree_item.text(i)))

        return name

    def get_tree_item_path_string(self, tree_item):
        """
        Returns full path of the given QTreeWidgetItem from its parent into it with the following format:
        "parent/parent/item"
        :param tree_item:
        :return:
        """

        parents = self.get_tree_item_path(tree_item)
        parent_names = self.get_tree_item_names(parents)

        if not parent_names:
            return
        if len(parent_names) == 1 and not parent_names[0]:
            return

        names = list()

        for name in parent_names:
            names.append(name[0])

        names.reverse()

        item_path_str = string.join(names, '/')

        return item_path_str

    def get_tree_item_path(self, tree_item):
        """
        Return the tree path of the given QTreeWidgetItem in a list starting from the given item
        :param tree_item: QTreeWidgetItem
        :return: list<QTreeWidgetItem>
        """

        if not tree_item:
            return

        parent_items = list()
        parent_items.append(tree_item)

        try:
            # When selecting an item in the tree and refreshing a C++ wrapped will raise
            parent_item = tree_item.parent()
        except Exception:
            parent_item = None

        while parent_item:
            parent_items.append(parent_item)
            parent_item = parent_item.parent()

        return parent_items

    def get_tree_item_names(self, tree_items):
        """
        Returns a list with the names of the given QTreeWidgetItems
        :param tree_items: list<QTreeWidgetItem>
        :return: list<str>
        """

        item_names = list()
        if not tree_items:
            return item_names

        for tree_item in tree_items:
            name = self.get_tree_item_name(tree_item)
            if name:
                item_names.append(name)

        return item_names

    def get_tree_item_children(self, tree_item):
        """
        Returns all child items of the given QTreeWidgetItem
        :param tree_item: QTreeWidgetItem
        :return: list<QTreeWidgetItem>
        """

        count = tree_item.childCount()
        items = list()
        for i in range(count):
            items.append(tree_item.child(i))

        return items

    def delete_empty_children(self, tree_item):
        """
        Deletes all given QTreeWidget child items that are empty (has no text)
        :param tree_item: QTreeWidgetItem
        """

        count = tree_item.childCount()
        if count <= 0:
            return

        for i in range(count):
            item = tree_item.child(i)
            if item and not item.text(0):
                item = tree_item.takeChild(i)
                del item

    def delete_tree_item_children(self, tree_item):
        """
        Deletes all given QTreeWidget chlid items
        :param tree_item: QTreeWidgetItem
        """

        count = tree_item.childCount()
        if count <= 0:
            return

        children = tree_item.takeChildren()
        for child in children:
            del child

    def _paint_drop_indicator(self, painter):
        """
        Internal function used to paint the drop indicator manually
        :param painter: QPainter
        """

        if self.state() == QAbstractItemView.DraggingState:
            opt = QStyleOption()
            opt.initFrom(self)
            opt.rect = self._drop_indicator_rect
            rect = opt.rect

            color = Qt.black
            if tp.is_maya():
                color = Qt.white

            brush = QBrush(QColor(color))
            pen = QPen(brush, 1, Qt.DotLine)
            painter.setPen(pen)
            if rect.height() == 0:
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                painter.drawRect(rect)

    def _edit_start(self, item):
        """
        Internal function that is called when a user start editing a tree item text
        Closes already opened edit text editors and updates internal variables
        :param item: QTreeWidgetItem
        """

        self._old_name = str(item.text(self._title_text_index))
        self.closePersistentEditor(item, self._title_text_index)
        self.openPersistentEditor(item, self._title_text_index)
        self._edit_state = item

        return

    def _edit_finish(self, item):
        """
        Internal function that is called when a text element of the tree is edited
        Checks that that edit mode is on text and updates the item text manually
        :param item: QTreeWidgetItem
        :return: QTreeWidgetItem, edited item
        """

        if not hasattr(self._edit_state, 'text'):
            return

        self._edit_state = None

        if type(item) == int:
            return self._current_item

        self.closePersistentEditor(item, self._title_text_index)
        state = self._item_rename_valid(self._old_name, item)

        if state:
            state = self._item_renamed(item)
            if not state:
                item.setText(self._title_text_index, self._old_name)
                return item
        else:
            item.setText(self._title_text_index, self._old_name)
            return item

        return item

    def _item_rename_valid(self, old_name, item):
        """
        Checks if the rename operation on a specific item of the tree is valid or not
        :param old_name: str, old name of the item
        :param item: QTreeWidgetItem, item that is being edit
        :return: bool
        """

        new_name = item.text(self._title_text_index)
        if not new_name:
            return False

        # We do not allow duplicated names on the tree
        if self._already_exists(item):
            return False

        if old_name == new_name:
            return False

        return True

    def _already_exists(self, item):
        """
        Checks if a given QTreeWidgetItem already exists on the tree.
        :param item: QTreeWidgetItem
        :return: bool
        """

        name = item.text(0)
        parent = item.parent()

        if parent:
            skip_index = parent.indexOfChild(item)
            for i in range(parent.childCount()):
                if i == skip_index:
                    continue
                other_name = str(parent.child(i).text(0))
                if name == other_name:
                    return True
        else:
            skip_index = self.indexFromItem(item)
            skip_index = skip_index.row()
            for i in range(self.topLevelItemCount()):
                if skip_index == i:
                    continue
                other_name = str(self.topLevelItem(i).text(0))
                if name == other_name:
                    return True

        return False

    def _clear_selection(self):
        """
        Internal function used to clear the selection of the tree and update internal variables
        """

        self.clearSelection()
        self._current_item = None
        if self._edit_state:
            self._edit_finish(self._last_item)

    def _emit_item_click(self, item):
        """
        Internal function that is used to force the emission of itemClicked signal
        :param item: QTreeWidgetItem
        """

        if item:
            name = item.text(self._title_text_index)
        else:
            name = ''

        self.itemClicked.emit(item, 0)

    def _get_ancestors(self, item):
        """
        Returns all ancestors items of the given QTreeWidgetItem
        :param item: QTreeWidgetItem
        :return: list<QTreeWidgetItem>
        """

        child_count = item.childCount()
        items = list()
        for i in range(child_count):
            child = item.child(i)
            children = self._get_ancestors(child)
            items.append(child)
            if children:
                items += children

        return items

    def _add_sub_items(self, tree_item):
        """
        Internal function that is updates the hiearchy of the given QTreeWidgetItem
        Implementation MUST be implemented in child class
        :param tree_item: QTreeWidgetItem
        """

        pass

    def _item_renamed(self, item):
        """
        Internal function that rename a specific QTreeWidgetItem contents
        Implementation MUST be implemented in child class
        :param item: QTreeWidgetItem
        """

        return False

    def _on_item_expanded(self, item):
        """
        Internal function that is called anytime the user expands an item of the tree
        Load dynamically all the items parented to the expanded item
        :param item: QTreeWidgetItem
        """

        if self._auto_add_sub_items:
            self._add_sub_items(item)

    def _on_item_collapsed(self, item):
        """
        Internal function that is called anytime the user collapses an item of the tree
        :param item: QTreeWidgetItem
        """

        pass

    def _on_item_activated(self, item):
        """
        Internal function that is called anytime a tree item is activated
        :param item: QTreeWidgetItem
        """

        if self._edit_state:
            self._edit_finish(self._edit_state)
        else:
            if self._text_edit:
                self._edit_start(item)

    def _on_item_changed(self, current_item, previous_item):
        """
        Internal function that is called when a tree item changes its content
        :param current_item: QTreeWidetItem
        :param previous_item: QTreeWidgetItem
        """

        if self._edit_state:
            self._edit_finish(previous_item)

    def _on_item_selection_changed(self):
        """
        Internal function that is called anytime the user changes the selection of the tree
        """

        item_sel = self.selectedItems()
        current_item = None
        if item_sel:
            current_item = item_sel[0]

        if current_item:
            self._current_name = current_item.text(self._title_text_index)
        if self._edit_state:
            self._edit_finish(self._edit_state)

        if not current_item:
            self._emit_item_click(current_item)

        self.SelectionChanged.emit()

    def _on_item_clicked(self, item, column):
        """
        Internal function that is called anytime the user clicks on an item of the tree
        Updates internal variables and clear the selection if necessary
        :param item: QTreeWidgetItem
        :param column: int
        """

        self._last_item = self._current_item
        self._current_item = self.currentItem()
        if not item or column != self._title_text_index:
            if self._last_item:
                self._clear_selection()


class ManageTreeWidget(base.BaseWidget, object):
    def __init__(self, parent=None):
        self.tree_widget = None
        super(ManageTreeWidget, self).__init__(parent)

    def set_tree_widget(self, tree_widget):
        """
        Set the tree widget managed by this widget
        :param tree_widget: QTreeWidget
        """

        self.tree_widget = tree_widget


class FilterTreeWidget(base.DirectoryWidget, object):
    NameFilterChanged = Signal(object)

    def __init__(self, parent=None):
        self.tree_widget = None
        self.emit_changes = True
        self.update_tree = True
        super(FilterTreeWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(FilterTreeWidget, self).ui()

        self.filter_names = search.SearchFindWidget()
        self.filter_names.set_placeholder_text('Filter Names')
        self.main_layout.addWidget(self.filter_names)

    def setup_signals(self):
        self.filter_names.textChanged.connect(self._on_filter_names)

    def get_name_filter(self):
        """
        Returns the name filter current text
        :return: str
        """

        return str(self.filter_names.text())

    def set_emit_changes(self, flag):
        """
        Sets whether signals should be emitted or not
        :param flag: bool
        """

        self.emit_changes = flag

    def set_name_filter(self, text):
        """
        Sets the name filter text
        :param text: str
        """

        self.filter_names.setText(text)

    def clear_name_filter(self):
        """
        Clears current name filter text
        """

        self.filter_names.setText('')

    def set_tree_widget(self, tree_widget):
        """
        Sets the tree widget used by this widget
        :param tree_widget: QTreeWidget
        """

        self.tree_widget = tree_widget

    def _on_filter_names(self, text):
        """
        Internal function that is used to call the filter function of the TreeWidget
        :param text: str, filter text that should be used
        """

        if self.update_tree:
            self.tree_widget.filter_names(text)


class FilterTreeDirectoryWidget(base.DirectoryWidget, object):
    SubPathChanged = Signal(object)
    NameFilterChanged = Signal(object)

    def __init__(self, parent=None):
        self.tree_widget = None
        self.emit_changes = True
        self.update_tree = True
        super(FilterTreeDirectoryWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(FilterTreeDirectoryWidget, self).ui()

        self.filter_names = search.SearchFindWidget()
        self.filter_names.set_placeholder_text('Filter Names')
        # self.filter_names.setPlaceholderText('Filter Names')

        self.sub_path_filter = QLineEdit()
        self.sub_path_filter.setPlaceholderText('Set Sub Path')
        self.sub_path_filter.setVisible(False)

        self.main_layout.addWidget(self.filter_names)
        self.main_layout.addWidget(self.sub_path_filter)

    def setup_signals(self):
        self.sub_path_filter.textChanged.connect(self._on_sub_path_filter_changed)
        self.sub_path_filter.textEdited.connect(self._on_sub_path_filter_edited)
        self.filter_names.textChanged.connect(self._on_filter_names)

    def get_name_filter(self):
        """
        Returns the name filter current text
        :return: str
        """

        return str(self.filter_names.text())

    def get_sub_path_filter(self):
        """
        Returns the sub path filter current text
        :return: str
        """

        return str(self.sub_path_filter.text())

    def set_emit_changes(self, flag):
        """
        Sets whether signals should be emitted or not
        :param flag: bool
        """

        self.emit_changes = flag

    def set_name_filter(self, text):
        """
        Sets the name filter text
        :param text: str
        """

        self.filter_names.setText(text)

    def set_sub_path_filter(self, text):
        """
        Sets the sub path filter text
        :param text: str
        """

        self.sub_path_filter.setText(text)

    def clear_name_filter(self):
        """
        Clears current name filter text
        """

        self.filter_names.setText('')

    def clear_sub_path_filter(self):
        """
        Clears current sub path filter text
        """

        self.sub_path_filter.setText('')

    def set_tree_widget(self, tree_widget):
        """
        Sets the tree widget used by this widget
        :param tree_widget: QTreeWidget
        """

        self.tree_widget = tree_widget

    def set_sub_path_warning(self, flag):
        """
        Updates the style of the sub path QLineEdit depending on the app that uses this widget
        :param flag: bool
        """

        if flag:
            if not tp.is_maya():
                self.sub_path_filter.setStyleSheet('background-color: rgb(255, 150, 150);')
            else:
                self.sub_path_filter.setStyleSheet('background-color: rgb(255, 100, 100);')
        else:
            self.sub_path_filter.setStyleSheet('')

    def _on_filter_names(self, text):
        """
        Internal function that is used to call the filter function of the TreeWidget
        :param text: str, filter text that should be used
        """

        if self.update_tree:
            self.tree_widget.filter_names(text)

    def _on_sub_path_filter_edited(self):
        """
        Internal function that is called anytime the user edit the filter text
        Emits proper signal with the new filter text
        """

        if not self.emit_changes:
            return

        current_text = str(self.sub_path_filter.text()).strip()
        self.SubPathChanged.emit(current_text)

    def _on_sub_path_filter_changed(self):
        """
        Internal function that is called anytime filter text is changed
        Updates the directory used by the tree and updates the tree if necessary
        """

        current_text = str(self.sub_path_filter.text()).strip()
        if not current_text:
            self.set_directory(self.directory)
            if self.update_tree:
                self.tree_widget.set_directory(self.directory)
            text = self.filter_names.text()
            self._on_filter_names(text)
            return

        sub_dir = path.join_path(self.directory, current_text)
        if not sub_dir:
            return

        if path.is_dir(sub_dir):
            if self.update_tree:
                self.tree_widget.set_directory(sub_dir)
            text = self.filter_names.text()
            self._on_filter_names(text)

        if self.emit_changes:
            self.SubPathChanged.emit(current_text)

# ======================================================================================================


class FileTreeWidget(TreeWidget, object):

    refreshed = Signal()

    HEADER_LABELS = ['Name', 'Size MB', 'Time']
    NEW_ITEM_NAME = 'new_file'
    NEW_ITEM_WIDGET = QTreeWidgetItem
    EXCLUDE_EXTENSIONS = list()

    def __init__(self, parent=None):
        self._directory = None
        super(FileTreeWidget, self).__init__(parent)

        self.setHeaderLabels(self.HEADER_LABELS)

    def _add_sub_items(self, tree_item):
        """
        Implements _add_sub_items() functionality
        :param tree_item: QTreeWidgetItem
        """

        # Clean item hierarchy first
        self.delete_empty_children(tree_item)
        self.delete_tree_item_children(tree_item)

        path_str = self.get_tree_item_path_string(tree_item)
        full_path_str = path.join_path(self._directory, path_str)
        files = self._get_files(full_path_str)

        self._add_items(files, tree_item)

    def get_item_directory(self, tree_item):
        """
        Returns the full path of the given tree item
        :param tree_item: QTreeWidgetItem
        :return: str
        """

        path_str = self.get_tree_item_path_string(tree_item)
        return path.join_path(self._directory, path_str)

    def set_directory(self, directory, refresh=True):
        """
        Sets the directory used by this QTreeWidget
        :param directory: str, directory
        :param refresh: bool, Whether to refresh QTreeWidget items after setting working directory
        """

        qt.logger.debug('Setting Tree directory: {}'.format(directory))

        self._directory = directory
        if refresh:
            self.refresh()

    def create_item(self, name=None):
        """
        Creates a new item (folder) inside the selected item
        :param name: str, name of the new item
        """

        current_item = self._current_item
        if current_item:
            item_path = self.get_tree_item_path_string(self._current_item)
            item_path = path.join_path(self._directory, item_path)
            if path.is_file(item_path):
                item_path = path.get_dirname(item_path)
                current_item = self._current_item.parent()
        else:
            item_path = self._directory

        if not name:
            name = self.NEW_ITEM_NAME

        folder.create_folder(name=name, directory=item_path)

        if current_item:
            self._add_sub_items(current_item)
            self.setItemExpanded(current_item, True)
        else:
            self.refresh()

    def delete_item(self):
        """
        Deletes the selected item
        """

        item = self._current_item
        item_path = self.get_item_directory(item)
        name = path.get_basename(item_path)
        item_directory = path.get_dirname(item_path)

        if path.is_dir(item_path):
            folder.delete_folder(name, item_directory)
        elif path.is_file(item_path):
            fileio.delete_file(name, item_directory)
            if item_path.endswith('.py'):
                fileio.delete_file(name + '.c', item_directory)

        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)

    def refresh(self):
        """
        Refreshes all QTreeWidget items
        """

        if not self._directory:
            self.clear()
            return

        files = self._get_files()
        if not files:
            self.clear()
            return

        self._load_files(files)
        self.refreshed.emit()

    def _get_files(self, directory=None):
        """
        Internal function taht returns  all files located in the given directory. If not directory is given, stored
         variable directory will be used
        :return: list<str>
        """

        if directory is None:
            directory = self._directory

        return folder.get_files_and_folders(directory)

    def _load_files(self, files):
        """
        Internal function that adds given files into the tree (clearing the tree first)
        :param files: list<str>
        """

        self.clear()
        self._add_items(files)

    def _add_items(self, files, parent=None):
        """
        Internal function that adds given files into the tree
        :param files: list<str>, list of files to add
        :param parent: QTreeWidgetItem, parent item to append new item
        :return:
        """

        for f in files:
            if parent:
                self._add_item(f, parent)
            else:
                self._add_item(f)

    def _add_item(self, file_name, parent=None):
        """
        Internal function that adds given file into the tree
        :param file_name: str, name of the file new item will store
        :param parent: QTreeWidgetItem, parent item to append new item into
        :return: QTreeWidet, new item added
        """

        try:
            self.blockSignals(True)
            self.clearSelection()
        finally:
            self.blockSignals(False)

        path_name = file_name
        found = False

        # Check if item exists
        if parent:
            parent_path = self.get_tree_item_path_string(parent)
            path_name = '{}/{}'.format(parent_path, file_name)
            for i in range(parent.childCount()):
                item = parent.child(i)
                if item.text(0) == file_name:
                    found = item
        else:
            for i in range(self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item.text(0) == file_name:
                    found = item

        # Check if the item should be excluded or not from the tree
        exclude = self.EXCLUDE_EXTENSIONS
        if exclude:
            split_name = file_name.split('.')
            extension = split_name[-1]
            if extension in exclude:
                return

        if found:
            item = found
        else:
            item = self.ITEM_WIDGET()

        # Constrain item size if necessary
        size = self.ITEM_WIDGET_SIZE
        if size:
            size = QSize(*size)
            item.setSizeHint(self._title_text_index, size)

        # Set item text
        item_path = path.join_path(self._directory, path_name)
        sub_files = folder.get_files_and_folders(item_path)
        item.setText(self._title_text_index, file_name)

        # Retrieve file properties
        if path.is_file(item_path):
            size = fileio.get_file_size(item_path)
            date = fileio.get_last_modified_date(item_path)
            item.setText(self._title_text_index + 1, str(size))
            item.setText(self._title_text_index + 2, str(date))

        # Update valid sub files
        # NOTE: Sub files are added dynamically when the user expands an item
        if sub_files:
            self.delete_tree_item_children(item)
            exclude_extensions = self.EXCLUDE_EXTENSIONS
            exclude_count = 0
            if exclude_extensions:
                for f in sub_files:
                    for exclude in exclude_extensions:
                        if f.endswith(exclude):
                            exclude_count += 1
                            break

            if exclude_count != len(sub_files):
                QTreeWidgetItem(item)

        # Add item to tree hierarchy
        if parent:
            parent.addChild(item)
        else:
            self.addTopLevelItem(item)

        try:
            self.blockSignals(True)
            self.setCurrentItem(item)
        finally:
            self.blockSignals(False)

        return item

    def get_tree_widget(self):
        """
        Returns TreeWidget being used by this widget
        Overrides to use custom TreeWidgets
        :return: QTreeWidget
        """

        return FileTreeWidget()

    def get_manager_widget(self):
        """
        Returns the widet that manages the tree widget
        :return: ManageTreeWidget
        """

        return ManageTreeWidget()

    def get_filter_widget(self):
        """
        Returns the filter widget used to filter tree contents
        :return: FilterTreeWidget
        """

        return FilterTreeDirectoryWidget()


class EditFileTreeWidget(base.DirectoryWidget, object):

    itemClicked = Signal(object, object)
    description = 'EditTree'

    TREE_WIDGET = FileTreeWidget
    MANAGER_WIDGET = ManageTreeWidget
    FILTER_WIDGET = FilterTreeWidget

    def __init__(self, parent=None):
        super(EditFileTreeWidget, self).__init__(parent)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def ui(self):
        super(EditFileTreeWidget, self).ui()

        self.tree_widget = self.TREE_WIDGET()

        self.manager_widget = self.MANAGER_WIDGET()
        self.manager_widget.set_tree_widget(self.tree_widget)

        self.filter_widget = self.FILTER_WIDGET()
        self.filter_widget.set_tree_widget(self.tree_widget)
        self.filter_widget.set_directory(self.directory)
        drag_reorder_icon = tp.ResourcesMgr().icon('drag_reorder')
        self.edit_mode_btn = buttons.IconButton(
            icon=drag_reorder_icon, icon_padding=2, button_style=buttons.ButtonStyles.FlatStyle)
        self.edit_mode_btn.setCheckable(True)
        self.edit_mode_btn.setMaximumHeight(20)
        self.edit_mode_btn.setMaximumWidth(40)
        self.filter_widget.main_layout.addWidget(self.edit_mode_btn)

        self.main_layout.addWidget(self.filter_widget)
        self.main_layout.addWidget(self.tree_widget)
        self.main_layout.addWidget(self.manager_widget)

        self._on_edit(False)

    def setup_signals(self):
        self.edit_mode_btn.toggled.connect(self._on_edit)
        self.tree_widget.itemClicked.connect(self._on_item_selection_changed)

    def set_directory(self, directory):
        """
        Overrides set_directory function to take in account also the sub path
        and update all directories of the different tree widgets
        :param directory: str
        :param sub_path: str
        """

        super(EditFileTreeWidget, self).set_directory(directory)
        self.filter_widget.set_directory(directory)
        self.tree_widget.set_directory(directory)

        if hasattr(self.manager_widget, 'set_directory'):
            self.manager_widget.set_directory(directory)

    def get_current_item(self):
        """
        Returns the current selected item on the tree
        :return: TreeItem
        """

        return self.tree_widget.current_item

    def get_current_item_name(self):
        """
        Returns the current name of the selected item on the tree
        :return: str
        """

        return self.tree_widget.current_name

    def get_current_item_directory(self):
        """
        Returns the directory the current selected item points to
        :return: str
        """

        item = self.get_current_item()
        return self.tree_widget.get_item_directory(item)

    def enable_edit_mode(self):
        """
        Enables edit mode
        """

        if not self.edit_mode_btn.isChecked():
            self.edit_mode_btn.blockSignals(True)
            try:
                self.edit_mode_btn.setChecked(True)
            finally:
                self.edit_mode_btn.blockSignals(False)

        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)

    def disable_edit_mode(self):
        """
        Enables edit mode
        """

        if self.edit_mode_btn.isChecked():
            self.edit_mode_btn.blockSignals(True)
            try:
                self.edit_mode_btn.setChecked(False)
            finally:
                self.edit_mode_btn.blockSignals(False)

        self.tree_widget.setDragEnabled(False)
        self.tree_widget.setAcceptDrops(False)
        self.tree_widget.setDropIndicatorShown(False)

    def get_checked_children(self, tree_item):
        """
        Function that returns checked item children of the given tree item
        :param tree_item:
        :return:
        """

        if not tree_item:
            return

        expand_state = tree_item.isExpanded()
        tree_item.setExpanded(True)
        children = self.tree_widget.get_tree_item_children(tree_item)

        checked_children = list()
        for child in children:
            check_state = child.checkState(0)
            if check_state == Qt.Checked:
                checked_children.append(child)
        levels = list()
        if checked_children:
            levels.append(checked_children)

        while children:
            new_children = list()
            checked_children = list()
            for child in children:
                current_check_state = child.checkState(0)
                if current_check_state != Qt.Checked:
                    continue
                child.setExpanded(True)
                sub_children = self.tree_widget.get_tree_item_children(child)
                checked = list()
                for sub_child in sub_children:
                    check_state = sub_child.checkState(0)
                    if check_state == Qt.Checked:
                        checked.append(sub_child)
                if sub_children:
                    new_children += sub_children
                if checked:
                    checked_children += checked
            if not checked_children:
                children = list()
                continue

        tree_item.setExpanded(expand_state)
        levels.reverse()

        return levels

    def refresh(self):
        """
        Refresh TreeWidget items
        """

        self.tree_widget.refresh()

    def _on_item_selection_changed(self):
        """
        Internal function that is called anytime the user selects an item on the TreeWidget
        Emits itemClicked signal with the name of the selected item and the item itself
        """

        items = self.tree_widget.selectedItems()
        name = None
        item = None
        if items:
            item = items[0]
            name = item.text(0)
            self.itemClicked.emit(name, item)

        return name, item

    def _on_edit(self, flag):
        """
        Internal function that is called anytime the user presses the Edit button on the filter widget
        If edit is ON, drag/drop operations in tree widget are disabled
        :param flag: bool
        """

        if flag:
            self.enable_edit_mode()
        else:
            self.disable_edit_mode()


class TreeWidgetItem(QTreeWidgetItem, object):
    def __init__(self, parent=None):
        self.widget = self.get_widget()
        if self.widget:
            self.widget.item = self
        self.column = self.get_column()
        super(TreeWidgetItem, self).__init__(parent)

    def get_widget(self):
        return None

    def get_column(self):
        return 0
