#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains generic functionality when dealing with projects
"""

from __future__ import print_function, division, absolute_import

import os
import logging

from Qt.QtCore import Qt, Signal, QSize
from Qt.QtWidgets import QSizePolicy, QWidget, QFrame, QPushButton, QMenu, QAction, QAbstractItemView
from Qt.QtGui import QPixmap, QIcon

from tpDcc import dcc
from tpDcc.managers import resources
from tpDcc.core import project as core_project
from tpDcc.core import consts
from tpDcc.libs.python import path, settings, folder, fileio
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts, search, directory, dividers, buttons, label, tabs, lineedit

LOGGER = logging.getLogger('tpDcc-libs-qt')


def get_project_by_name(projects_path, project_name, project_class=None):
    """
    Returns a project located in the given path and with the given name (if exists)
    :param projects_path: str
    :param project_name: str
    :param project_class: cls
    :return: Project or None
    """

    if not projects_path or not os.path.isdir(projects_path):
        LOGGER.warning('Projects Path "{}" does not exist!'.format(projects_path))
        return None

    all_projects = get_projects(projects_path, project_class=project_class)
    for project in all_projects:
        if project.name == project_name:
            return project

    return None


def get_projects(projects_path, project_class=None):
    """
    Returns all projects located in given path
    :param projects_path: str
    :param project_class: cls
    :return: list(Project)
    """

    if not project_class:
        project_class = Project

    projects_found = list()

    if not projects_path or not os.path.isdir(projects_path):
        LOGGER.warning('Projects Path {} is not valid!'.format(projects_path))
        return projects_found

    for root, dirs, files in os.walk(projects_path):
        if consts.PROJECTS_NAME in files:
            new_project = project_class.create_project_from_data(
                path.join_path(root, consts.PROJECTS_NAME))
            if new_project is not None:
                projects_found.append(new_project)

    return projects_found


class Project(base.BaseWidget):
    projectOpened = Signal(object)
    projectRemoved = Signal()
    projectImageChanged = Signal(str)

    def __init__(self, project_data, parent=None):

        self._project_data = project_data

        super(Project, self).__init__(parent)

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def name(self):
        return self._project_data.name

    @property
    def path(self):
        return self._project_data.path

    @property
    def full_path(self):
        return self._project_data.full_path

    @property
    def settings(self):
        return self._project_data.settings

    @property
    def project_data(self):
        return self._project_data

    # ============================================================================================================
    # CLASS FUNCTIONS
    # ============================================================================================================

    @classmethod
    def create_project_from_data(cls, project_data_path):
        """
        Creates a new project using a project data JSON file
        :param project_data_path: str, path where project JSON data file is located
        :return: Project
        """

        if project_data_path is None or not path.is_file(project_data_path):
            LOGGER.warning('Project Data Path {} is not valid!'.format(project_data_path))
            return None

        project_data = settings.JSONSettings()
        project_options = settings.JSONSettings()
        project_dir = path.get_dirname(project_data_path)
        project_name = path.get_basename(project_data_path)
        project_data.set_directory(project_dir, project_name)
        project_options.set_directory(project_dir, 'options.json')
        if not project_data or not project_data.has_settings():
            LOGGER.warning('No valid project data found on Project Data File: {}'.format(project_data_path))

        project_name = project_data.get('name')
        project_path = path.get_dirname(path.get_dirname(project_data_path))
        project_image = project_data.get('image')

        LOGGER.debug('New Project found [{}]: {}'.format(project_name, project_path))
        project_data = core_project.ProjectData(
            name=project_name, project_path=project_path, settings=project_data, options=project_options)

        new_project = cls(project_data=project_data)
        if project_image:
            new_project.set_image(project_image)

        return new_project

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def ui(self):
        super(Project, self).ui()

        self.setMaximumWidth(qtutils.dpi_scale(160))
        self.setMaximumHeight(qtutils.dpi_scale(200))

        widget_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        self.project_btn = QPushButton('', self)
        self.project_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.project_btn.setIconSize(QSize(120, 120))
        project_lbl = label.BaseLabel(self.name, parent=self)
        project_lbl.setObjectName('projectLabel')
        project_lbl.setAlignment(Qt.AlignCenter)
        widget_layout.addWidget(self.project_btn)
        widget_layout.addWidget(project_lbl)

    def setup_signals(self):
        self.project_btn.clicked.connect(self._on_open_project)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        remove_icon = resources.icon(name='delete')
        remove_action = QAction(remove_icon, 'Remove', menu)
        remove_action.setStatusTip(consts.DELETE_PROJECT_TOOLTIP)
        remove_action.setToolTip(consts.DELETE_PROJECT_TOOLTIP)
        remove_action.triggered.connect(self._on_remove_project)

        folder_icon = resources.icon(name='open_folder', extension='png')
        folder_action = QAction(folder_icon, 'Open in Browser', menu)
        folder_action.setStatusTip(consts.OPEN_PROJECT_IN_EXPLORER_TOOLTIP)
        folder_action.setToolTip(consts.OPEN_PROJECT_IN_EXPLORER_TOOLTIP)
        folder_action.triggered.connect(self._on_open_in_browser)

        image_icon = resources.icon(name='picture', extension='png')
        set_image_action = QAction(image_icon, 'Set Project Image', menu)
        set_image_action.setToolTip(consts.SET_PROJECT_IMAGE_TOOLTIP)
        set_image_action.setStatusTip(consts.SET_PROJECT_IMAGE_TOOLTIP)
        set_image_action.triggered.connect(self._on_set_project_image)

        for action in [remove_action, None, folder_action, None, set_image_action]:
            if action is None:
                menu.addSeparator()
            else:
                menu.addAction(action)

        menu.exec_(self.mapToGlobal(event.pos()))

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def open(self):
        """
        Opens project
        """

        self._on_open_project()

    def has_option(self, name, group=None):
        """
        Returns whether the current object has given option or not
        :param name: str, name of the option
        :param group: variant, str || None, group of the option (optional)
        :return: bool
        """

        if not self._project_data:
            return False

        return self._project_data.has_option(name=name, group=group)

    def add_option(self, name, value, group=None, option_type=None):
        """
        Adds a new option to the options file
        :param name: str, name of the option
        :param value: variant, value of the option
        :param group: variant, str || None, group of the option (optional)
        :param option_type: variant, str || None, option type (optional)
        """

        if not self._project_data:
            return

        self._project_data.add_option(name, value, group=group, option_type=option_type)

    def get_option(self, name, group=None, default=None):
        """
        Returns option by name and group
        :param name: str, name of the option we want to retrieve
        :param group: variant, str || None, group of the option (optional)
        :return: variant
        """

        if not self._project_data:
            return

        return self._project_data.get_option(name, group=group, default=default)

    def reload_options(self):
        """
        Reload settings
        """

        if not self._project_data:
            return

        self._project_data.reload_options()

    def clear_options(self):
        """
        Clears all the options
        """

        if not self._project_data:
            return

        self._project_data.clear_options()

    def set_image(self, encoded_image):

        from tpDcc.libs.qt.core import image

        if not encoded_image:
            return

        encoded_image = encoded_image.encode('utf-8')
        self.project_btn.setIcon(QIcon(QPixmap.fromImage(image.base64_to_image(encoded_image))))

    def remove(self):

        from tpDcc.libs.qt.core import qtutils

        if not path.is_dir(self.full_path):
            LOGGER.warning('Impossible to remove Project Path: {}'.format(self.full_path))
            return False

        project_name = self.project_data.name
        project_path = self.project_data.path

        result = qtutils.get_permission(message='Are you sure you want to delete project: {}'.format(self.name),
                                        title='Deleting Project', cancel=False)
        if not result:
            return

        valid_delete = folder.delete_folder(folder_name=project_name, directory=project_path)
        if valid_delete is None:
            return False

        return True

    def load_project_data(self):
        """
        Return dictionary data contained in the project
        :return: dict
        """

        if not self.settings:
            return

        return self.settings.data()

    def get_project_nodes(self):
        """
        Returns path where nodes should be stored
        :return: str
        """

        return [os.path.join(self.full_path, 'nodes'), os.path.join(self.full_path, 'components')]

    def get_options(self):
        """
        Returns all options contained in the project
        :return: str
        """

        return self._project_data.get_options()

    def get_project_image(self):
        """
        Returns the image used by the project
        :return: QPixmap
        """

        return self._project_data.get_project_image()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_open_project(self):
        """
        Internal callback function that is called when a project is opened
        """

        LOGGER.debug('Loading project "{}" ...'.format(self.full_path))
        self.projectOpened.emit(self)

    def _on_remove_project(self):
        """
        Internal callback function that is called when a project is removed
        """

        valid_remove = self.remove()
        if valid_remove:
            self.projectRemoved.emit()

    def _on_open_in_browser(self):
        """
        Internal callback function that is called when a project is browsed
        """

        fileio.open_browser(self.full_path)

    def _on_set_project_image(self):
        """
        Internal callback function that is called when project image is set
        """

        image_file = dcc.select_file_dialog(
            title='Select Project Image File',
            pattern="PNG Files (*.png)")

        if image_file is None or not path.is_file(image_file):
            LOGGER.warning('Selected Image "{}" is not valid!'.format(image_file))
            return

        valid_change = self._project_data.set_project_image(image_file)

        if valid_change:
            self.projectImageChanged.emit(image_file)


class ProjectViewer(base.BaseWidget, object):
    projectOpened = Signal(object)

    def __init__(self, project_class, parent=None):
        self._settings = None
        self._project_class = project_class
        super(ProjectViewer, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.FlowLayout(parent=self, spacing_x=0, spacing_y=0)
        return main_layout

    def set_settings(self, settings):
        """
        Set the settings used by this editor
        This settings come from the main UI settings
        :param settings: QtIniSettings
        """

        self._settings = settings
        self.update_projects()

    def add_project(self, project_widget):
        if project_widget is None:
            return

        project_widget.projectOpened.connect(self._on_open_project)
        project_widget.projectRemoved.connect(self._on_removed_project)
        project_widget.projectImageChanged.connect(self._on_updated_project_image)

        self.main_layout.addWidget(project_widget)

    def get_widgets(self):
        all_widgets = list()

        for i in range(self.main_layout.count()):
            widget_item = self.main_layout.itemAt(i)
            if not widget_item:
                continue
            w = widget_item.widget()
            all_widgets.append(w)

        return all_widgets

    def get_project_by_name(self, project_name):
        for w in self.get_widgets():
            if w.name == project_name:
                return w

        return None

    def update_projects(self, project_path=None):

        qtutils.clear_layout(self.main_layout)

        # self.clear()

        if not project_path:
            if self._settings is None:
                LOGGER.debug('No Projects Path defined yet ...')
                return
            if self._settings.has_setting('project_directory'):
                project_path = self._settings.get('project_directory')

        projects_found = get_projects(project_path, project_class=self._project_class)
        for project_found in projects_found:
            self.add_project(project_found)

    def _on_open_project(self, project):
        self.projectOpened.emit(project)

    def _on_removed_project(self):
        self.update_projects()

    def _on_updated_project_image(self, image_path):
        self.update_projects()


class ProjectWidget(QWidget, object):

    PROJECT_CLASS = Project

    projectOpened = Signal(object)

    def __init__(self, settings=None, parent=None):
        super(ProjectWidget, self).__init__(parent=parent)

        self._settings = None
        self._history = None

        main_layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))
        self.setLayout(main_layout)

        self._tab_widget = tabs.BaseTabWidget(parent=self)
        self._open_project = OpenProjectWidget(project_class=self.PROJECT_CLASS)
        self._new_project = NewProjectWidget(project_class=self.PROJECT_CLASS)
        self._tab_widget.addTab(self._open_project, 'Projects')
        self._tab_widget.addTab(self._new_project, 'New Project')
        main_layout.addWidget(self._tab_widget)

        self._open_project.projectOpened.connect(self._on_project_opened)
        self._new_project.projectCreated.connect(self._on_project_created)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        self.set_settings(settings)

    def set_settings(self, settings):
        """
        Set the settings used by this editor
        This settings come from the main UI settings
        :param settings: QtIniSettings
        """

        self._settings = settings
        self._open_project.set_settings(settings)
        self._new_project.set_settings(settings)

    def set_projects_path(self, projects_path):
        """
        Sets the path where we want to search for projects
        :param projects_path: str
        """

        self._open_project.set_projects_path(projects_path)

    def get_project_by_name(self, project_name, force_update=True):
        """
        Returns project by its name
        :param project_name: str
        :param force_update: bool
        :return: Project
        """

        if force_update:
            self._open_project.get_projects_list().update_projects()

        projects_list = self._open_project.get_projects_list()
        return projects_list.get_project_by_name(project_name)

    def open_project(self, project_name):
        """
        Opens project with given name
        :param project_name: str
        :return: Project
        """

        project_found = self.get_project_by_name(project_name)
        if project_found:
            project_found.open()
            return project_found

    def _on_project_opened(self, project):
        self.projectOpened.emit(project)

    def _on_project_created(self, project):
        self._tab_widget.setCurrentIndex(0)

    def _on_tab_changed(self, index):
        if index == 0:
            self._open_project.update_projects()


class OpenProjectWidget(base.BaseWidget, object):
    projectOpened = Signal(object)

    def __init__(self, project_class, parent=None):

        self._project_class = project_class
        self._settings = None

        super(OpenProjectWidget, self).__init__(parent=parent)

        self._update_ui()

    def get_main_layout(self):
        return layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

    def ui(self):
        super(OpenProjectWidget, self).ui()

        self._search_widget = search.SearchFindWidget()
        self._search_widget.set_placeholder_text('Filter Projects ...')

        self._projects_list = ProjectViewer(project_class=self._project_class)
        self._projects_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        buttons_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        buttons_layout.setAlignment(Qt.AlignCenter)

        buttons_layout1 = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        buttons_layout1.setAlignment(Qt.AlignLeft)
        self._browse_widget = directory.SelectFolder(label_text='Projects Path', use_app_browser=True, use_icon=True)
        buttons_layout1.addWidget(self._browse_widget)

        buttons_layout.addLayout(buttons_layout1)

        self.main_layout.addWidget(self._search_widget)
        self.main_layout.addWidget(dividers.Divider('PROJECTS', alignment=Qt.AlignCenter))
        self.main_layout.addWidget(self._projects_list)
        self.main_layout.addLayout(buttons_layout)

    def setup_signals(self):
        self._search_widget.textChanged.connect(self._on_search_project)
        self._browse_widget.directoryChanged.connect(self._on_directory_browsed)
        self._projects_list.projectOpened.connect(self._on_project_opened)

    def get_projects_list(self):
        """
        Returns projects list widget
        :return: ProjectViewer
        """

        return self._projects_list

    def set_projects_path(self, projects_path):
        """
        Sets the path where we want to search for projects
        :param projects_path: str
        """

        self._on_directory_browsed(projects_path)
        self.update_projects(projects_path)

    def set_settings(self, settings):
        """
        Set the settings used by this editor
        This settings come from the main UI settings
        :param settings: QtIniSettings
        """

        self._settings = settings
        self._update_ui()

        # We set the settings of the projects list after updating UI
        self._projects_list.set_settings(settings)

    def update_projects(self, project_path=None):
        self._projects_list.update_projects(project_path=project_path)

    def _update_ui(self, project_path=None):
        """
        Update UI based on the stored settings if exists
        """

        if not project_path:
            if self._settings:
                if self._settings.has_setting('project_directory'):
                    project_path = self._settings.get('project_directory')
                    LOGGER.debug('Project Path stored in settings: {}'.format(project_path))

        if project_path:
            self._browse_widget.set_directory(directory=project_path)
            if self._settings:
                self.update_projects()
            else:
                self.update_projects(project_path=project_path)

    def _on_search_project(self, project_text):
        for project in self._projects_list.get_widgets():
            project.setVisible(project_text.lower() in project.name.lower())

    def _on_directory_browsed(self, dir):
        """
        Set the project directory
        :param dir: str
        """

        if not dir or not path.is_dir(dir):
            return

        if self._settings:
            self._settings.set('project_directory', dir)
            LOGGER.debug('Updated FactoRig Project Path: {}'.format(dir))
            self._update_ui()
        else:
            self._update_ui(dir)

    def _on_project_opened(self, project):
        self.projectOpened.emit(project)


class NewProjectWidget(base.BaseWidget, object):
    projectCreated = Signal(object)

    def __init__(self, project_class, parent=None):

        self._settings = None
        self._selected_template = None
        self._project_class = project_class

        super(NewProjectWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        return layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

    def ui(self):
        super(NewProjectWidget, self).ui()

        self._search_widget = search.SearchFindWidget()
        self._search_widget.set_placeholder_text('Filter Templates ...')

        self._templates_list = TemplatesViewer(project_class=self._project_class)
        self._templates_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        project_layout = layouts.HorizontalLayout(spacing=1, margins=(0, 0, 0, 0))

        project_line_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        project_layout.addLayout(project_line_layout)
        self._project_line = lineedit.BaseLineEdit(parent=self)
        self._project_line.setPlaceholderText('Project Path')
        self._project_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._project_btn = directory.SelectFolderButton(text='', use_app_browser=True)
        project_line_layout.addWidget(self._project_line)
        project_line_layout.addWidget(self._project_btn)
        self._name_line = lineedit.BaseLineEdit(parent=self)
        self._name_line.setPlaceholderText('Project Name')
        project_line_layout.addWidget(dividers.get_horizontal_separator_widget())
        project_line_layout.addWidget(self._name_line)
        self._create_btn = buttons.BaseButton('Create', parent=self)
        self._create_btn.setIcon(resources.icon('create'))
        project_line_layout.addSpacing(10)
        project_line_layout.addWidget(self._create_btn)

        self.main_layout.addWidget(self._search_widget)
        self.main_layout.addWidget(dividers.Divider('TEMPLATES', alignment=Qt.AlignCenter))
        self.main_layout.addWidget(self._templates_list)
        self.main_layout.addLayout(project_layout)

    def setup_signals(self):
        self._search_widget.textChanged.connect(self._on_search_template)
        self._templates_list.selectedTemplate.connect(self._on_selected_template)
        self._project_btn.directoryChanged.connect(self._on_directory_browsed)
        self._create_btn.clicked.connect(self._on_create)

    @property
    def templates_list(self):
        return self._templates_list

    def set_settings(self, settings):
        """
        Set the settings used by this editor
        This settings come from the main UI settings
        :param settings: QtIniSettings
        """

        self._settings = settings
        self._update_ui()

    def _update_ui(self):
        """
        Update UI based on the stored settings if exists
        """

        if self._settings:
            if self._settings.has_setting('project_directory'):
                project_path = self._settings.get('project_directory')
                self._project_line.setText(project_path)
                self._project_btn.init_directory = project_path

    def _on_search_template(self, template_text):
        for template in self._templates_list.get_widgets():
            template.setVisible(template_text.lower() in template.name.lower())

    def _on_selected_template(self, template):
        self._selected_template = template

    def _on_directory_browsed(self, dir):
        if not dir or not path.is_dir(dir):
            return

        self._project_line.setText(str(dir))

    def _on_create(self):
        project_path = self._project_line.text()
        project_name = self._name_line.text()
        if not project_path or not path.is_dir(project_path) or not project_name:
            LOGGER.warning('Project Path: {} or Project Name: {} are not valid!'.format(project_path, project_name))
            return
        if self._selected_template is None:
            LOGGER.warning('No Template selected, please select one first ...')
            return

        new_project = self._selected_template.create_project(project_name=project_name, project_path=project_path)
        if new_project is not None:
            LOGGER.debug(
                'Project {} created successfully on path {}'.format(new_project.name, new_project.path))
            self._name_line.setText('')
            self.projectCreated.emit(new_project)
            return new_project

        return None


class TemplateData(object):

    PROJECT_CLASS = None

    def __init__(self, name='New Template'):
        self._name = name

    def get_name(self):
        return self._name

    name = property(get_name)

    def create_project(self, project_name, project_path):
        if not self.PROJECT_CLASS:
            LOGGER.warning('Impossible to create because project class is not defined!')
            return None

        project_data = settings.JSONSettings()
        project_options = settings.JSONSettings()
        LOGGER.debug('New Project found [{}]: {}'.format(project_name, project_path))
        project_data = core_project.ProjectData(
            name=project_name, project_path=project_path, settings=project_data, options=project_options)
        project_data.create_project()

        new_project = self.PROJECT_CLASS(project_data=project_data)

        return new_project


class Template(base.BaseWidget):
    templateChecked = Signal(object)

    def __init__(self, parent=None):
        super(Template, self).__init__(parent=parent)

    def ui(self):
        super(Template, self).ui()

        self.setMaximumWidth(160)
        self.setMaximumHeight(200)

        widget_layout = layouts.VerticalLayout(spacing=0, margins=(2, 2, 2, 2))
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setLineWidth(1)
        main_frame.setLayout(widget_layout)
        self.main_layout.addWidget(main_frame)

        self.template_btn = QPushButton('', self)
        self.template_btn.setCheckable(True)
        self.template_btn.setIcon(self.get_icon())
        self.template_btn.setIconSize(QSize(120, 120))
        template_lbl = label.BaseLabel(self.name, parent=self)
        template_lbl.setObjectName('templateLabel')
        template_lbl.setAlignment(Qt.AlignCenter)
        widget_layout.addWidget(self.template_btn)
        widget_layout.addWidget(template_lbl)

    def setup_signals(self):
        self.template_btn.toggled.connect(self._on_selected_template)

    def get_icon(self):
        return resources.icon(name='project', extension='png')

    def _on_selected_template(self, template):
        self.templateChecked.emit(self)


class BlankTemplateData(TemplateData, object):
    def __init__(self, name='Blank'):
        super(BlankTemplateData, self).__init__(name=name)

    def get_name(self):
        return self._name

    name = property(get_name)

    def create_project(self, project_name, project_path):
        new_project = super(
            BlankTemplateData, self).create_project(project_name=project_name, project_path=project_path)
        new_project.project_data.create_folder(consts.DATA_FOLDER)
        new_project.project_data.create_folder(consts.CODE_FOLDER)
        return new_project


class BlankTemplate(Template, BlankTemplateData):
    def __init__(self, parent=None):
        BlankTemplateData.__init__(self)
        Template.__init__(self, parent=parent)


class TemplatesViewer(base.BaseWidget, object):

    STANDARD_TEMPLATES = [BlankTemplate]
    selectedTemplate = Signal(object)

    def __init__(self, project_class, parent=None):
        self._project_class = project_class
        super(TemplatesViewer, self).__init__(parent=parent)

        self._init_standard_templates()

    def get_main_layout(self):
        main_layout = layouts.FlowLayout(parent=self)
        return main_layout

    def get_widgets(self):
        all_widgets = list()

        for i in range(self.main_layout.count()):
            widget_item = self.main_layout.itemAt(i)
            if not widget_item:
                continue
            w = widget_item.widget()
            all_widgets.append(w)

        return all_widgets

    def add_template(self, template_widget):
        if template_widget is None:
            return

        template_widget.PROJECT_CLASS = self._project_class
        template_widget.templateChecked.connect(self._on_template_selected)

        self.main_layout.addWidget(template_widget)

    def clear_templates(self):
        qtutils.clear_layout(self.main_layout)

    def _init_standard_templates(self):
        for template in self.STANDARD_TEMPLATES:
            new_template = template()
            self.add_template(new_template)

    def _on_template_selected(self, template):
        self.selectedTemplate.emit(template)
