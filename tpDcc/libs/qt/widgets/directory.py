#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with directories and files
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs import qt
from tpDcc.libs.python import path
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import buttons


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
    directoryChanged = Signal(object)   # Signal that is called when a new folder is selected

    def __init__(self, text='Browse', directory='', use_app_browser=False, parent=None):
        super(SelectFolderButton, self).__init__(parent)

        self._use_app_browser = use_app_browser
        self._directory = directory
        self.settings = None

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        folder_icon = tp.ResourcesMgr().icon('folder')
        self._folder_btn = buttons.IconButton(
            icon=folder_icon, icon_padding=2, button_style=buttons.ButtonStyles.FlatStyle)
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
            raise NotImplementedError(
                'Open Folder Browser Dialog is not impelented in your current DCC: {}'.format(tp.Dcc.get_name()))

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

        self._folder_label = QLabel(
            '{0}'.format(self._label_text)) if self._label_text == '' else QLabel('{0}:'.format(self._label_text))
        self._folder_line = FolderEditLine()
        self._folder_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if os.path.exists(self._directory):
            self._folder_line.setText(self._directory)

        if self._use_icon:
            folder_icon = tp.ResourcesMgr().icon('folder')
            self._folder_btn = buttons.IconButton(
                icon=folder_icon, icon_padding=2, button_style=buttons.ButtonStyles.FlatStyle)
        else:
            self._folder_btn = buttons.StyleBaseButton('Browse...')
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

        if tp.is_maya():
            import tpDcc.dccs.maya as maya
            result = maya.cmds.fileDialog2(
                caption='Select Folder', fileMode=3, startingDirectory=self.folder_line.text())
            if result:
                result = result[0]
            if not result or not os.path.isdir(result):
                return
            else:
                filename = path.clean_path(result)
                self.set_directory(filename)
                self._text_changed()
        else:
            raise NotImplementedError(
                'Open Folder Browser Dialog is not implemented in your current DCC: {}'.format(tp.Dcc.get_name()))

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


class SelectFile(base.DirectoryWidget, object):
    """
    Widget with button and line edit that opens a file dialog to select file paths
    """

    directoryChanged = Signal(object)  # Signal that is called when a new folder is selected

    def __init__(self, label_text='Select File', directory='', use_app_browser=False,
                 filters=None, use_icon=True, parent=None):

        self._use_app_browser = use_app_browser
        self.settings = None
        self._use_icon = use_icon
        self._directory = directory
        self._label_text = label_text
        self._filters = filters

        super(SelectFile, self).__init__(parent)

    @property
    def file_label(self):
        return self._file_label

    @property
    def file_line(self):
        return self._file_line

    @property
    def file_btn(self):
        return self._folder_btn

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        return main_layout

    def ui(self):
        super(SelectFile, self).ui()

        self._file_label = QLabel('{0}'.format(self._label_text)) if self._label_text == '' else QLabel(
            '{0}:'.format(self._label_text))
        self._file_line = FolderEditLine()
        self._file_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if self._directory and os.path.exists(self._directory):
            self._file_line.setText(self._directory)

        if self._use_icon:
            folder_icon = tp.ResourcesMgr().icon('folder')
            self._file_btn = buttons.IconButton(
                icon=folder_icon, icon_padding=2, button_style=buttons.ButtonStyles.FlatStyle)
        else:
            self._file_btn = buttons.StyleBaseButton('Browse ...')

        for widget in [self._file_label, self._file_line, self._file_btn]:
            self.main_layout.addWidget(widget)

    def setup_signals(self):
        self._file_btn.clicked.connect(self._open_file_browser_dialog)
        self._file_line.textChanged.connect(self._text_changed)

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

    def set_directory(self, directory):
        """
        Sets the text of the directory line
        :param directory: str
        """

        super(SelectFile, self).set_directory(directory=directory)

        self._file_line.setText(directory)

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

        if tp.is_maya():
            import tpDcc.dccs.maya as maya

            file_line = self._file_line.text()
            if os.path.isfile(file_line):
                file_line = os.path.dirname(file_line)
            result = maya.cmds.fileDialog2(
                caption='Select File', fileMode=1, fileFilter=self._filters or '', startingDirectory=file_line)
            if result:
                result = result[0]
            if not result or not os.path.isfile(result):
                qt.logger.warning('Selected file {} is not a valid file!'.format(result))
                return
            else:
                filename = path.clean_path(result)
                self._file_line.setText(filename)
                self.directoryChanged.emit(filename)
                self.update_settings(filename=filename)
        else:
            raise NotImplementedError(
                'Select File Dialog is not implemented in your current DCC: {}'.format(tp.Dcc.get_name()))

        return filename

    def _text_changed(self):
        """
        This function is called each time the user manually changes the line text
        :param directory: str, new edit line text after user edit
        """

        f = self.get_directory()
        if path.is_file(f):
            self.directoryChanged.emit(f)


class GetDirectoryWidget(base.DirectoryWidget, object):
    directoryChanged = Signal(object)
    textChanged = Signal(object)

    def __init__(self, parent=None):

        self._label = 'directory'
        self._show_files = False

        super(GetDirectoryWidget, self).__init__(parent=parent)

    @property
    def show_files(self):
        return self._show_files

    def ui(self):
        super(GetDirectoryWidget, self).ui()

        self._directory_widget = QWidget()
        directory_layout = QHBoxLayout()
        self._directory_widget.setLayout(directory_layout)
        self.main_layout.addWidget(self._directory_widget)

        self._directory_lbl = QLabel('directory')
        self._directory_lbl.setMinimumWidth(60)
        self._directory_lbl.setMaximumWidth(100)
        self._directory_edit = QLineEdit()
        self._directory_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._directory_browse_btn = QPushButton('browse')

        directory_layout.addWidget(self._directory_lbl)
        directory_layout.addWidget(self._directory_edit)
        directory_layout.addWidget(self._directory_browse_btn)

    def setup_signals(self):
        self._directory_edit.textChanged.connect(self._on_text_changed)
        self._directory_browse_btn.clicked.connect(self._on_browse)

    def set_directory(self, directory):
        super(GetDirectoryWidget, self).set_directory(directory)
        self.set_directory_text(directory)

    def get_directory(self):
        return self._directory_edit.text()

    def set_label(self, label):
        length = len(label) * 8
        self._directory_lbl.setMinimumWidth(length)
        self._directory_lbl.setText(label)

    def set_directory_text(self, text):
        self._directory_edit.setText(text)

    def set_placeholder_text(self, text):
        self._directory_edit.setPlaceholderText(text)

    def set_example(self, text):
        self.set_placeholder_text('example: {}'.format(text))

    def set_error(self, flag):

        if tp.is_maya():
            yes_color = QColor(0, 255, 0, 50)
            no_color = QColor(255, 0, 0, 50)
        else:
            yes_color = QColor(200, 255, 200, 100)
            no_color = QColor(25, 200, 200, 100)

        palette = QPalette()
        if flag:
            palette.setColor(QPalette().Base, no_color)
        else:
            palette.setColor(QPalette().Base, yes_color)

        self._directory_edit.setPalette(palette)

    def _on_text_changed(self, text):
        directory = self.get_directory()
        if os.path.exists(directory):
            self.set_error(False)
        else:
            self.set_error(True)

        if not text:
            self._directory_edit.setPalette(QLineEdit().palette())

        self.directoryChanged.emit(directory)

    def _on_browse(self):
        directory = self.get_directory()
        if not directory:
            placeholder = self._directory_edit.placeholderText()
            if placeholder and placeholder.startswith('example: '):
                example_path = placeholder[0]
                if os.path.exists(example_path):
                    directory = example_path

        filename = qtutils.get_folder(directory, show_files=self._show_files, parent=self)
        filename = path.clean_path(filename)
        if filename and path.is_dir(filename):
            self._directory_edit.setText(filename)
            self.directoryChanged.emit(filename)
