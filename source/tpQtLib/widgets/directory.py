#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with directories and files
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpQtLib
import tpDccLib as tp
from tpPyUtils import path
from tpQtLib.widgets import button


class FileListWidget(QListWidget, object):
    """
    Widgets that shows files and directories such Windows Explorer
    """

    directory_activated = Signal(str)
    file_activated = Signal(str)
    file_selected = Signal(str)
    folder_selected = Signal(str)
    directory_selected = Signal(str)
    files_selected = Signal(list)
    up_requested = Signal()
    update_requested = Signal()

    def __init__(self, parent):
        self.parent = parent
        super(FileListWidget, self).__init__(parent)

        # region Signals
        self.itemSelectionChanged.connect(self.selectItem)
        self.itemDoubleClicked.connect(self.activateItem)
        # endregion

    # region Override Functions
    def resizeEvent(self, event):
        """
        Overrides QWidget resizeEvent so when the widget is resize a update request signal is emitted
        :param event: QResizeEvent
        """

        self.update_requested.emit()
        super(FileListWidget, self).resizeEvent(event)

    def wheelEvent(self, event):
        """
        Overrides QWidget wheelEvent to smooth scroll bar movement
        :param event: QWheelEvent
        """

        sb = self.horizontalScrollBar()
        minValue = sb.minimum()
        maxValue = sb.maximum()
        if sb.isVisible() and maxValue > minValue:
            sb.setValue(sb.value() + (-1 if event.delta() > 0 else 1))
        super(FileListWidget, self).wheelEvent(event)

    def keyPressEvent(self, event):
        """
        Overrides QWidget keyPressEvent with some shortcuts when using the widget
        :param event:
        :return:
        """
        modifiers = event.modifiers()
        if event.key() == int(Qt.Key_Return) and modifiers == Qt.NoModifier:
            if len(self.selectedItems()) > 0:
                item = self.selectedItems()[0]
                if item.type() == 0:  # directory
                    self.directory_activated.emit(item.text())
                else:  # file
                    self.file_activated.emit(item.text())
        elif event.key() == int(Qt.Key_Backspace) and modifiers == Qt.NoModifier:
            self.up_requested.emit()
        elif event.key() == int(Qt.Key_F5) and modifiers == Qt.NoModifier:
            self.update_requested.emit()
        else:
            super(FileListWidget, self).keyPressEvent(event)
    # endregion

    # region Public Functions
    def selectItem(self):
        if len(self.selectedItems()) > 0:
            item = self.selectedItems()[0]
            if item.type() == 0:    # directory
                self.folder_selected.emit(item.text())
            if item.type() == 1:  # file
                self.file_selected.emit(item.text())

    def activateItem(self):
        if len(self.selectedItems()) > 0:
            item = self.selectedItems()[0]
            if item.type() == 0:  # directory
                self.directory_activated.emit(item.text())
            else:  # file
                self.file_activated.emit(item.text())

    def setExtendedSelection(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.disconnect(self.selectItem)
        self.itemSelectionChanged.connect(self.processSelectionChanged)

    def processSelectionChanged(self):
        """
        Gets all selected items and emits a proper signal with the proper selected item names
        """

        items = filter(lambda x: x.type() != 0, self.selectedItems())
        names = map(lambda x: x.text(), items)
        self.files_selected.emit(names)
    # endregion


class FolderEditLine(QLineEdit, object):
    """
    Custom QLineEdit with drag and drop behaviour for files and folders
    """

    def __init__(self, parent=None):
        super(FolderEditLine, self).__init__(parent)

        self.setDragEnabled(True)
        self.setReadOnly(True)

    def dragEnterEvent(self, event):
        """
        Overrides QWidget dragEnterEvent to enable drop behaviour with file
        :param event: QDragEnterEvent
        :return:
        """
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            self.setText(urls[0].toLocalFile())


class SelectFolderButton(QWidget, object):
    """
    Button widget that allows to select folder paths
    """

    beforeNewDirectory = Signal()
    directoryChanged = Signal(object) # Signal that is called when a new folder is selected

    def __init__(self, text='Browse', directory='', use_app_browser=False, parent=None):
        super(SelectFolderButton, self).__init__(parent)

        self._use_app_browser = use_app_browser
        self._directory = directory
        self.settings = None

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        folder_icon = tpQtLib.resource.icon('folder')
        self._folder_btn = button.IconButton(icon=folder_icon, icon_padding=2, button_style=button.ButtonStyles.FlatStyle)
        main_layout.addWidget(self._folder_btn)

        self._folder_btn.clicked.connect(self._open_folder_browser_dialog)

    # region Properties
    @property
    def folder_btn(self):
        return self._folder_btn

    def get_init_directory(self):
        return self._directory

    def set_init_directory(self, directory):
        self._directory = directory

    init_directory = property(get_init_directory, set_init_directory)
    # endregion

    # region Public Functions
    def set_settings(self, settings):
        self.settings = settings
    # endregion

    # region Private Functions
    def _open_folder_browser_dialog(self):
        """
        Opens a set folder browser and returns the selected path
        :return: str, Path of the selected folder
        """

        self.beforeNewDirectory.emit()

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            result = cmds.fileDialog2(caption='Select Folder', fileMode=3, startingDirectory=self.init_directory)
            if result:
                result = result[0]
            else:
                return
        else:
            raise NotImplementedError('Open Folder Browser Dialog is not impelented in your current DCC: {}'.format(tp.Dcc.get_name()))

        self.directoryChanged.emit(result)
        # if not result or not os.path.isdir(result[0]):
        if not result or not os.path.isdir(result):
            return
        return path.clean_path(result[0])
    # endregion


class SelectFolder(QWidget, object):
    """
    Widget with button and line edit that opens a folder dialog to select folder paths
    """

    directoryChanged = Signal(object)  # Signal that is called when a new folder is selected

    def __init__(self, label_text='Select Folder', directory='', use_app_browser=False, use_icon=True, parent=None):
        super(SelectFolder, self).__init__(parent)

        self._use_app_browser = use_app_browser
        self._use_icon = use_icon
        self.settings = None
        self.directory = None
        self._label_text = label_text
        self._directory = directory

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        self._folder_label = QLabel('{0}'.format(self._label_text)) if self._label_text == '' else QLabel('{0}:'.format(self._label_text))
        self._folder_line = FolderEditLine()
        self._folder_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if os.path.exists(self._directory):
            self._folder_line.setText(self._directory)

        if self._use_icon:
            folder_icon = tpQtLib.resource.icon('folder')
            self._folder_btn = button.IconButton(icon=folder_icon, icon_padding=2, button_style=button.ButtonStyles.FlatStyle)
        else:
            self._folder_btn = button.BaseButton('Browse...')
        self._folder_btn.setMaximumHeight(20)

        for widget in [self._folder_label, self._folder_line, self._folder_btn]:
            main_layout.addWidget(widget)

        self._folder_btn.clicked.connect(self._open_folder_browser_dialog)

    @property
    def folder_label(self):
        return self._folder_label

    @property
    def folder_line(self):
        return self._folder_line

    @property
    def folder_btn(self):
        return self._folder_btn

    def set_directory_text(self, new_text):
        """
        Sets the text of the directory line
        :param new_text: str
        """

        self._folder_line.setText(new_text)

    def get_directory(self):
        """
        Returns directory set on the directory line
        :return: str
        """

        return str(self._folder_line.text())

    def set_directory(self, directory):
        """
        Sets the directory of the directory line
        """

        if not directory:
            return

        self.directory = directory

        self.set_directory_text(directory)

    def _open_folder_browser_dialog(self):
        """
        Opens a set folder browser and returns the selected path
        :return: str, Path of the selected folder
        """

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            result = cmds.fileDialog2(caption='Select Folder', fileMode=3, startingDirectory=self.folder_line.text())
            if result:
                result = result[0]
            if not result or not os.path.isdir(result):
                return
            else:
                filename = path.clean_path(result)
                self.set_directory(filename)
                self._text_changed()
        else:
            raise NotImplementedError('Open Folder Browser Dialog is not implemented in your current DCC: {}'.format(tp.Dcc.get_name()))

        return filename

    def _text_changed(self):
        """
        This function is called each time the user manually changes the line text
        Emits the signal to notify that the directory has changed
        :param directory: str, new edit line text after user edit
        """

        directory = self.get_directory()
        if path.is_dir(directory):
            self.directoryChanged.emit(directory)

    def _send_directories(self, directory):
        """
        Emit the directory changed signal with the given directory
        :param directory: str
        :return: str
        """

        self.directoryChanged.emit(directory)


class SelectFile(QWidget, object):
    """
    Widget with button and line edit that opens a file dialog to select file paths
    """

    directoryChanged = Signal(object)  # Signal that is called when a new folder is selected

    def __init__(self, label_text='Select File', directory='', use_app_browser=False, filters=None, use_icon=True, parent=None):
        super(SelectFile, self).__init__(parent)

        self._use_app_browser = use_app_browser
        self.settings = None
        self._use_icon = use_icon
        self._directory = directory
        self._label_text = label_text
        self._filters = filters

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        self._file_label = QLabel('{0}'.format(self._label_text)) if self._label_text == '' else QLabel(
            '{0}:'.format(self._label_text))
        self._file_line = FolderEditLine()
        self._file_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if os.path.exists(self._directory):
            self._file_line.setText(self._directory)

        if self._use_icon:
            folder_icon = tpQtLib.resource.icon('folder')
            self._file_btn = button.IconButton(icon=folder_icon, icon_padding=2, button_style=button.ButtonStyles.FlatStyle)
        else:
            self._file_btn = button.BaseButton('Browse ...')

        for widget in [self._file_label, self._file_line, self._file_btn]:
            main_layout.addWidget(widget)

        self._file_btn.clicked.connect(self._open_file_browser_dialog)

    @property
    def file_label(self):
        return self._file_label

    @property
    def file_line(self):
        return self._file_line

    @property
    def file_btn(self):
        return self._folder_btn

    def set_settings(self, settings):
        """
        Set new settings. Override in new classes to add custom behaviour
        :param settings:
        :return:
        """
        self.settings = settings

    def update_settings(self, filename):
        """
        Updates current settings. Override in new classes to add custom behaviour
        :param settings: new selected path for the user
        """

        pass

    def set_label(self, text):
        """
        Sets the directory label text
        :param text: str, new directory label text
        :return:
        """

        self._file_label.setText(text)

    def set_directory_text(self, new_text):
        """
        Sets the text of the directory line
        :param new_text: str
        """

        self._file_line.setText(new_text)

    def get_directory(self):
        """
        Returns directory setted on the directory line
        :return: str
        """

        return self._file_line.text()

    def _open_file_browser_dialog(self):
        """
        Opens a set folder browser and returns the selected path
        :return: str, Path of the selected folder
        """

        raise NotImplementedError('Not implemented yet to work in the proper way!')

        # TODO: Remove Maya dependency
        # result = cmds.fileDialog2(caption='Select File', fileMode=1, fileFilter=self._filters, startingDirectory=self._file_line.text())
        #
        # if result:
        #     result = result[0]
        # if not result or not os.path.isfile(result):
        #     tpQtLib.logger.warning('Selected file {} is not a valid file!'.format(result))
        #     return
        # else:
        #     filename = path.clean_path(result)
        #     self._file_line.setText(filename)
        #     self.directoryChanged.emit(filename)
        #     self.update_settings(filename=filename)
        #
        #     return filename

    def _text_changed(self):
        """
        This function is called each time the user manually changes the line text
        :param directory: str, new edit line text after user edit
        """

        f = self.get_directory()
        if path.is_file(f):
            self.directoryChanged.emit(f)