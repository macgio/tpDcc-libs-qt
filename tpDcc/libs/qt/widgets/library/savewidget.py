#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base save widget for items
"""

from __future__ import print_function, division, absolute_import

import os
import tempfile
import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs import qt
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts, buttons, directory, formwidget, messagebox, dividers, snapshot
from tpDcc.libs.qt.widgets.library import widgets


class BaseSaveWidget(base.BaseWidget, object):
    def __init__(self, item, settings, temp_path=None, parent=None):

        self._item = None
        self._settings = settings
        self._temp_path = temp_path
        self._options_widget = None

        super(BaseSaveWidget, self).__init__(parent=parent)

        self.setObjectName('LibrarySaveWidget')
        self.set_item(item)

    def ui(self):
        super(BaseSaveWidget, self).ui()

        title_layout = layouts.HorizontalLayout()
        title_layout.setContentsMargins(2, 2, 0, 0)
        title_layout.setSpacing(2)
        self._icon_lbl = QLabel()
        self._icon_lbl.setMaximumSize(QSize(14, 14))
        self._icon_lbl.setMinimumSize(QSize(14, 14))
        self._icon_lbl.setScaledContents(True)
        self._title_lbl = QLabel()
        title_layout.addWidget(self._icon_lbl)
        title_layout.addWidget(self._title_lbl)

        self._folder_widget = directory.SelectFolder('Folder', use_app_browser=True)

        buttons_layout = layouts.HorizontalLayout()
        buttons_layout.setContentsMargins(4, 4, 4, 4)
        buttons_layout.setSpacing(4)
        buttons_frame = QFrame()
        buttons_frame.setFrameShape(QFrame.NoFrame)
        buttons_frame.setFrameShadow(QFrame.Plain)
        buttons_frame.setLayout(buttons_layout)
        buttons_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.save_btn = buttons.BaseButton('Save')
        self.cancel_btn = buttons.BaseButton('Cancel')
        buttons_layout.addWidget(self.save_btn, parent=self)
        buttons_layout.addWidget(self.cancel_btn, parent=self)
        buttons_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self._options_layout = layouts.VerticalLayout()
        self._options_layout.setContentsMargins(0, 0, 0, 0)
        self._options_layout.setSpacing(2)
        self._options_frame = QFrame()
        self._options_frame.setFrameShape(QFrame.NoFrame)
        self._options_frame.setFrameShadow(QFrame.Plain)
        self._options_frame.setLineWidth(0)
        self._options_frame.setLayout(self._options_layout)

        self._extra_layout = layouts.VerticalLayout()
        self._extra_layout.setContentsMargins(0, 0, 0, 0)
        self._extra_layout.setSpacing(2)

        self.main_layout.addLayout(title_layout)
        self.main_layout.addWidget(self._folder_widget)
        self._extra_layout.addWidget(self._options_frame)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addLayout(self._extra_layout)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addWidget(buttons_frame)

    def setup_signals(self):
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self._on_cancel)

    def settings(self):
        """
        Returns settings object
        :return: JSONSettings
        """

        return self._settings

    def set_settings(self, settings):
        """
        Sets save widget settings
        :param settings: JSONSettings
        """

        self._settings = settings

    def item(self):
        """
        Returns the library item to be created
        :return: LibraryItem
        """

        return self._item

    def set_item(self, item):
        """
        Sets the base item to be created
        :param item: LibraryItem
        """

        self._item = item

        self._title_lbl.setText(item.MenuName)
        self._icon_lbl.setPixmap(QPixmap(item.type_icon_path()))
        schema = item.save_schema()
        if schema:
            options_widget = formwidget.FormWidget(self)
            options_widget.set_schema(schema)
            options_widget.set_validator(item.save_validator)
            self._options_frame.layout().addWidget(options_widget)
            self._options_widget = options_widget
            self.load_settings()
            options_widget.stateChanged.connect(self._on_options_changed)
            options_widget.validate()
        else:
            self._options_frame.setVisible(False)

    def library_window(self):
        """
        Returns library widget window for the item
        :return: LibraryWindow
        """

        return self._item.library_window()

    def set_library_window(self, library_window):
        """
        Sets the library widget for the item
        :param library_window: LibraryWindow
        """

        self._item.set_library_window(library_window)

    def name(self):
        """
        Returns the name of the field
        :return: str
        """

        return self._title_lbl.text().strip()

    def description(self):
        """
        Returns the string from the comment field
        :return: str
        """

        return self._comment.toPlainText().strip()

    def folder_frame(self):
        """
        Returns the frame that contains the folder edit, label and button
        :return: QFrame
        """

        return self._folder_frame

    def folder_path(self):
        """
        Returns the folder path
        :return: str
        """

        return self._folder_widget.folder_line.text()

    def set_folder_path(self, path):
        """
        Sets the destination folder path
        :param path: str
        """

        self._folder_widget.folder_line.setText(path)

    def default_values(self):
        """
        Returns all the default values for the save fields
        :return: dict
        """

        values = dict()
        for option in self.item().save_schema():
            values[option.get('name')] = option.get('default')

        return values

    def save_settings(self):
        """
        Saves the current state of the widget to disk
        """

        state = self._options_widget.options_state()
        self.settings().set(self.item().__class__.__name__, {'SaveOptions': state})

    def load_settings(self):
        """
        Returns the settings object for saving the state of the widget
        """

        option_settings = self.settings().get(self.item().__class__.__name__, {})
        options = option_settings.get('SaveOptions', dict())
        values = self.default_values()
        if options:
            for option in self.item().save_schema():
                name = option.get('name')
                persistent = option.get('persistent')
                if not persistent and name in options:
                    options[name] = values[name]
            self._options_widget.set_state_from_options(options)

    def save(self, path, icon_path, objects=None):
        """
        Saves the item with the given objects to the given disk location path
        :param path: list(str)
        :param icon_path: str
        :param objects: str
        """

        item = self.item()
        options = self._options_widget.values()

        item.save(path=path, objects=objects, icon_path=icon_path, **options)

        self.close()

    def _save(self):
        if not self.library_window():
            return

        try:
            path = self.folder_path()
            options = self._options_widget.values()
            name = options.get('name')
            objects = tp.Dcc.selected_nodes(full_path=True) or list()
            if not path:
                raise Exception('No folder selected. Please select a destination folder')
            if not name:
                raise Exception('No name specified. Please set a name before saving')

            if not os.path.exists(self.icon_path()):
                btn = self.show_thumbnail_capture_dialog()
                if btn == QDialogButtonBox.Cancel:
                    return

            path += '/{}'.format(name)
            icon_path = self.icon_path()

            self.save(path=path, icon_path=icon_path, objects=objects)

        except Exception as e:
            messagebox.MessageBox.critical(self.library_window(), 'Error while saving', str(e))
            qt.logger.error(traceback.format_exc())
            raise

        self.library_window().stack.slide_in_index(0)

    def _on_options_changed(self):
        """
        Internal callback function that is called when an option value changes
        """

        self.save_settings()

    def _on_save(self):
        if not self.library_window():
            return

        self._save()

        self.library_window().stack.slide_in_index(0)

    def _on_cancel(self):
        self.close()
        self.library_window().stack.slide_in_index(0)


class SaveWidget(BaseSaveWidget, object):
    def __init__(self, item, settings, temp_path=None, parent=None):

        self._script_job = None
        self._sequence_path = None
        self._icon_path = ''

        super(SaveWidget, self).__init__(item=item, settings=settings, temp_path=temp_path, parent=parent)

        self.create_sequence_widget()
        self.update_thumbnail_size()

        try:
            self._on_selection_changed()
            # self.set_script_job_enabled(True)
        except NameError as e:
            qt.logger.error('{} | {}'.format(e, traceback.format_exc()))

    def ui(self):
        super(SaveWidget, self).ui()

        model_panel_layout = layouts.HorizontalLayout()
        model_panel_layout.setContentsMargins(0, 0, 0, 0)
        model_panel_layout.setSpacing(0)
        thumbnail_layout = layouts.VerticalLayout()
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        thumbnail_layout.setSpacing(0)
        self._thumbnail_frame = QFrame()
        self._thumbnail_frame.setMinimumSize(QSize(50, 50))
        self._thumbnail_frame.setMaximumSize(QSize(150, 150))
        self._thumbnail_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._thumbnail_frame.setFrameShape(QFrame.NoFrame)
        self._thumbnail_frame.setFrameShadow(QFrame.Plain)
        self._thumbnail_frame.setLineWidth(0)
        self._thumbnail_frame.setLayout(thumbnail_layout)
        model_panel_layout.addWidget(self._thumbnail_frame)
        self._thumbnail_btn = QPushButton()
        self._thumbnail_btn.setMinimumSize(QSize(0, 0))
        self._thumbnail_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._thumbnail_btn.setMaximumSize(QSize(150, 150))
        self._thumbnail_btn.setToolTip('Take snapshot')
        self._thumbnail_btn.setStyleSheet(
            'color: rgb(40, 40, 40);border: 0px solid rgb(0, 0, 0, 150);background-color: rgb(254, 255, 230, 200);')
        self._thumbnail_btn.setIcon(tp.ResourcesMgr().icon('thumbnail'))
        self._thumbnail_btn.setToolTip("""
        Click to capture a thumbnail from the current viewport.\n
        CTRL + Click to show the capture window for better framing
        """)
        thumbnail_layout.addWidget(self._thumbnail_btn)

        self._extra_layout.addLayout(model_panel_layout)

    def setup_signals(self):
        super(SaveWidget, self).setup_signals()
        self._thumbnail_btn.clicked.connect(self._on_thumbnail_capture)

    def resizeEvent(self, event):
        """
        Overrides base QWidget resizeEvent function
        :param event: QResizeEvent
        """

        self.update_thumbnail_size()

    def icon_path(self):
        """
        Returns the icon path to be used for the thumbnail
        :return: str
        """

        return self._icon_path

    def set_icon(self, icon):
        """
        Sets the icon for the create widget thumbnail
        :param icon: QIcon
        """

        self._thumbnail_btn.setIcon(icon)
        self._thumbnail_btn.setIconSize(QSize(200, 200))
        self._thumbnail_btn.setText('')

    def sequence_path(self):
        """
        Returns the playblast path
        :return: str
        """

        return self._sequence_path

    def set_sequence_path(self, path):
        """
        Sets the disk location for the image sequence to be saved
        :param path: str
        """

        self._sequence_path = path
        self._thumbnail_btn.set_dirname(os.path.dirname(path))

    def create_sequence_widget(self):
        """
        Creates a sequence widget to replace the static thumbnail widget
        """

        sequence_widget = widgets.LibraryImageSequenceWidget(self)
        sequence_widget.setObjectName('thumbnailButton')
        sequence_widget.setStyleSheet(self._thumbnail_btn.styleSheet())
        sequence_widget.setToolTip(self._thumbnail_btn.toolTip())

        camera_icon = tp.ResourcesMgr().get('icons', 'camera.svg')
        expand_icon = tp.ResourcesMgr().get('icons', 'expand.svg')
        folder_icon = tp.ResourcesMgr().get('icons', 'folder.svg')

        sequence_widget.addAction(camera_icon, 'Capture new image', 'Capture new image', self._on_thumbnail_capture)
        sequence_widget.addAction(
            expand_icon, 'Show Capture window', 'Show Capture window', self._on_show_capture_window)
        sequence_widget.addAction(
            folder_icon, 'Load image from disk', 'Load image from disk', self._on_show_browse_image_dialog)

        sequence_widget.setIcon(tp.ResourcesMgr().icon('thumbnail2'))
        self._thumbnail_frame.layout().insertWidget(0, sequence_widget)
        self._thumbnail_btn.hide()
        self._thumbnail_btn = sequence_widget
        self._thumbnail_btn.clicked.connect(self._on_thumbnail_capture)

    def set_sequence(self, source):
        """
        Sets the sequenced path for the thumbnail widget
        :param source: str
        """

        self.set_thumbnail(source, sequence=True)

    def set_thumbnail(self, source, sequence=False):
        """
        Sets the thumbnail
        :param source: str
        :param sequence: bool
        """

        source = os.path.normpath(source)

        # TODO: Find a way to remove temp folder afteer saving the file
        # filename, extension = os.path.splitext(source)
        # with path_utils.temp_dir() as dir_path:
        # dir_path = path_utils.temp_dir()
        # target = os.path.join(dir_path, 'thumbnail{}'.format(extension))
        # shutil.copyfile(source, target)
        # tpQtLib.logger.debug('Source Thumbnail: {}'.format(source))
        # tpQtLib.logger.debug('Target Thumbnail: {}'.format(target))
        # self._icon_path = target
        # self._thumbnail_btn.set_path(target)

        self._icon_path = source
        self._thumbnail_btn.set_path(source)

        if sequence:
            self.set_sequence_path(source)

    def update_thumbnail_size(self):
        """
        Updates the thumbnail button to teh size of the widget
        """

        width = self.width() - 10
        if width > 250:
            width = 250
        size = QSize(width, width)
        self._thumbnail_btn.setIconSize(size)
        self._thumbnail_btn.setMaximumSize(size)
        self._thumbnail_frame.setMaximumSize(size)

    def show_by_frame_dialog(self):
        """
        Show the by frame dialog
        """

        help_text = """
        To help speed up the playblast you can set the "by frame" to another greather than 1.
        For example if the "by frame" is set to 2 it will playblast every second frame
        """

        options = self._options_widget.values()
        by_frame = options.get('byFrame', 1)
        start_frame, end_frame = options.get('frameRange', [None, None])
        duration = 1
        if start_frame is not None and end_frame is not None:
            duration = end_frame - start_frame
        if duration > 100 and by_frame == 1:
            buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            result = messagebox.MessageBox.question(
                self.library_window(), title='Tip', text=help_text, buttons=buttons, enable_dont_show_checkbox=True
            )
            if result != QDialogButtonBox.Ok:
                raise Exception('Cancelled by user')

    def show_thumbnail_capture_dialog(self):
        """
        Asks the user if they would like to capture a thumbnail
        :return: int
        """

        buttons = QDialogButtonBox.Yes | QDialogButtonBox.Ignore | QDialogButtonBox.Cancel
        parent = self.item().library_window()
        btn = messagebox.MessageBox.question(
            None, 'Create a thumbnail', 'Would you like to capture a thumbnail?', buttons=buttons)
        if btn == QDialogButtonBox.Yes:
            self.thumbnail_capture()

        return btn

    def thumbnail_capture(self, show=False):
        """
        Captures a playblast and saves it to the temporal thumbnail path
        :param show: bool
        """

        options = self._options_widget.values()
        start_frame, end_frame = options.get('frameRange', [None, None])
        step = options.get('byFrame', 1)

        if not qtutils.is_control_modifier():
            self.show_by_frame_dialog()

        if not self._temp_path or not os.path.isdir(self._temp_path):
            self._temp_path = tempfile.mkdtemp()
        self._temp_path = os.path.join(self._temp_path, 'thumbnail.jpg')

        try:
            snapshot.SnapshotWindow(path=self._temp_path, on_save=self._on_thumbnail_captured)
            # thumbnail.ThumbnailCaptureDialog.thumbnail_capture(
            #     path=self._temp_path,
            #     show=show,
            #     start_frame=start_frame,
            #     end_frame=end_frame,
            #     step=step,
            #     clear_cache=False,
            #     captured=self._on_thumbnail_captured
            # )
        except Exception as e:
            messagebox.MessageBox.critical(self.library_window(), 'Error while capturing thumbnail', str(e))
            qt.logger.error(traceback.format_exc())

    def save(self, path, icon_path, objects=None):
        """
        Saves the item with the given objects to the given disk location path
        :param path: list(str)
        :param icon_path: str
        :param objects: str
        """

        item = self.item()
        options = self._options_widget.values()
        sequence_path = self.sequence_path()
        if sequence_path:
            sequence_path = os.path.dirname(sequence_path)

        item.save(path=path, objects=objects, icon_path=icon_path, sequence_path=sequence_path, **options)

        self.close()

    def _on_selection_changed(self):
        """
        Internal callback functino that is called when DCC selection changes
        """

        if self._options_widget:
            self._options_widget.validate()

    def _on_thumbnail_capture(self):
        self.thumbnail_capture(show=False)

    def _on_thumbnail_captured(self, captured_path):
        """
        Internal callback function that is called when thumbnail is captured
        :param captured_path: str
        """

        self.set_sequence(captured_path)

    def _on_show_capture_window(self):
        """
        Internal callback function that shows the capture window for framing
        """

        self.thumbnail_capture(show=True)

    def _on_show_browse_image_dialog(self):
        """
        Internal callback function that shows a file dialog for choosing an image from disk
        """

        file_dialog = QFileDialog(self, caption='Open Image', filter='Image Files (*.png *.jpg)')
        file_dialog.fileSelected.connect(self.set_thumbnail)
        file_dialog.exec_()
