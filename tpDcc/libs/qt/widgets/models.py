#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base classes for Qt models
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *


class ItemSelection(QItemSelection):
    """
    Extends QItemSelection functionality for view items
    """

    def __init__(self, *args):
        super(ItemSelection, self).__init__(*args)

    # region Override Functions
    def indexes(self):
        """
        Override QItemSelection indexes() method

        :warning: Specific to Qt 4.7.0 the QModelIndexList destructor will cause a destructor crash.
            This method avoids that crash by overriding the indexes() method and manually building
            the index list with a python builtin list.
        :seealso: http://www.qtcentre.org/threads/16933
        :return: list<QModelIndex>, list of model indexes corresponding to the selected items
        """

        indexes = list()
        for i in range(self.count()):
            parent = self[i].parent()
            for c in range(self[i].left(), self[i].right() + 1):
                for r in range(self[i].top(), self[i].bottom() + 1):
                    indexes.append(self[i].model().index(r, c, parent))

        return indexes


class ListModel(QAbstractListModel, object):
    def __init__(self, data=None, parent=None):
        """
        Basic model for string lists
        :param data: list<string>, list of string items to add to the model
        :param parent: QWidget
        """

        if data is None:
            data = list()

        super(ListModel, self).__init__(parent=parent)
        self._items = data

    def headerData(self):
        return None

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the length of the internal collection item list
        """

        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        """
        Returns the number of columns in this model
        """

        return 1

    def flags(self, index):
        """
        Gets the Qt.ItemFlags for the model data at a given index
        :param index: int, lookup key for the data
        :return: A valid combination of the Qt.Flags enum
        """

        # return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.item(index)

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets the model data at a given index, filtered by the given role to the value
        """

        return False

    def insertRows(self, position, rows, parent=QModelIndex()):
        """
        Inserts a row with empty AbstractDataItems into the model
        """

        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self._items.insert(position, 'test')
        self.endInsertRows()

        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        """
        Removes a row from the model
        """

        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            value = self._items[position]
            self._items.remove(value)
        self.endRemoveRows()
        return True

    def clear(self):
        """
        Clears all data model
        """

        try:
            self._items.clear()
        except Exception:
            del self._items[:]

    def item(self, index):
        """
        Returns the internal data item given the index
        :param index: int, QModelIndex representing the index
        :return: item if the index is valid, None otherwise
        """

        if isinstance(index, (int, long)):
            return self._items[index]

        if isinstance(index, QModelIndex) and index.isValid():
            item = index.internalPointer()
            if item:
                return item
            return self._items[index.row()]

        return None

    def set_items(self, items):
        """
        Clears current model items and adds new ones
        :param items: list<string>, items to add to the model
        """

        self.clear()
        for item in items:
            self.append_item(item)

    def append_item(self, item):
        """
        Appends an existing AbstractDataItem into the model
        :param item: AbstractDataItem
        :return: bool
        """

        next_index = self.rowCount()
        last_index = next_index
        self.beginInsertRows(QModelIndex(), next_index, last_index)
        self._item_insert(item)
        self.endInsertRows()
        return True

    def _item_insert(self, item=None):
        """
        Internal function that inserts an item into the internal collection
        :param item: object, item to append to end of the internal collection
        """

        self._items.append(item)

    def _item_insert_position(self, item, index):
        """
        Internal item insert at specific index position
        :param item: object, item to append to end of the internal collection
        :param index: int, internal index of the item in the internal collection
        """

        self._items.insert(index, item)

    def _item_remove(self, item):
        """
        Internal item removal
        :param item: the item to remove from the internal collection
        """

        try:
            self._items.remove(item)
        except ValueError:
            pass

    def _item_remove_position(self, index):
        """
        Internal remove item at specific index position in the internal collection
        :param index: int, index of the item to remove from the internal collection
        """

        try:
            item = self._items.pop(index)
        except IndexError:
            pass


class TableModel(QAbstractTableModel, object):
    def __init__(self, data=[], horizontal_headers=[], vertical_headers=[], parent=None):
        """
        Basic model for table models
        :param data: list<list>, multi dimensional array in row-column order
        :param parent: QWidget
        """

        super(TableModel, self).__init__(parent=parent)
        self._items = data
        self._headers = {
            Qt.Horizontal: horizontal_headers,
            Qt.Vertical: vertical_headers
        }

    # region Override Functions
    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        header_data = self._headers.get(orientation, None)
        return header_data[section] if header_data else None

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the length of the internal collection item list
        """

        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        """
        Returns the length of the first element of the internal collection item list
        """

        return len(self._headers[Qt.Horizontal])

    def flags(self, index):
        """
        Gets the Qt.ItemFlags for the model data at a given index
        :param index: int, lookup key for the data
        :return: A valid combination of the Qt.Flags enum
        """

        # return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):

        if role == Qt.DisplayRole:
            return self.item(index=index)

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets the model data at a given index, filtered by the given role to the value
        """

        return False

    def insertRows(self, position, rows, parent=QModelIndex()):
        """
        Inserts a new item into the table
        """

        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            default_values = ['' for i in range(self.columnCount())]
            self._items.insert(position, default_values)
        self.endInsertRows()

        return True

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        row_count = len(self._items)
        for i in range(columns):
            for j in range(row_count):
                self._items[j].insert(position, '')
        self.endInsertColumns()

        return True
    # endregion

    # region Public Functions
    def clear(self):
        """
        Clears all data model
        """

        try:
            self._items.clear()
        except Exception:
            del self._items[:]

    def item(self, index):
        """
        Returns the internal data item given the index
        :param index: int, QModelIndex representing the index
        :return: item if the index is valid, None otherwise
        """

        if isinstance(index, (int, long)):
            return self._items[index]

        if isinstance(index, QModelIndex) and index.isValid():
            item = index.internalPointer()
            if item:
                return item

            if len(self._items) > 0:
                return self._items[index.row()][index.column()]
        return None

    def set_items(self, items):
        """
        Clears current model items and adds new ones
        :param items: list<list>, items to add to teh model
        """

        self.clear()
        for item in items:
            self.append_item(item=item)

    def append_item(self, item):
        """
        Appends an existing AbstractDataItem into the model
        :param item: AbstractDataItem
        :return: bool
        """

        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._item_insert(item)
        self.endInsertRows()

        return True
    # endregion

    # region Private Functions
    def _item_insert(self, item):
        """
        Internal function that inserts an item into the internal collection
        :param item: object, item to append to end of the internal collection
        """

        self._items.append(item)

    def _item_insert_position(self, item, index):
        """
        Internal item insert at specific index position
        :param item: object, item to append to end of the internal collection
        :param index: int, internal index of the item in the internal collection
        """

        self._items.insert(index, item)
