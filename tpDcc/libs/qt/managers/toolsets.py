#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for DCC toolsets
"""

import os
from collections import OrderedDict

import tpDcc
from tpDcc.core import plugin
from tpDcc.libs.python import python, decorators, folder, yamlio, color
from tpDcc.libs.qt.widgets import toolset

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader


class ToolsetsPluginsManager(plugin.PluginsManager, object):

    INTERFACE = toolset.ToolsetWidget

    def __init__(self):
        super(ToolsetsPluginsManager, self).__init__()


class ToolsetsManager(object):
    def __init__(self,):
        super(ToolsetsManager, self).__init__()

        self._toolsets = dict()
        self._toolset_groups = dict()
        self._registered_paths = dict()

        self._manager = ToolsetsPluginsManager()

    @property
    def toolset_groups(self):
        return self._toolset_groups

    def register_path(self, package_name, path_to_register):
        """
        Register path to find toolsets from
        :return: str
        """

        if not path_to_register or not os.path.isdir(path_to_register):
            return None

        if package_name not in self._registered_paths:
            self._registered_paths[package_name] = list()

        if path_to_register not in self._registered_paths[package_name]:
            self._registered_paths[package_name].append(path_to_register)

    # ============================================================================================================
    # TOOLSETS
    # ============================================================================================================

    def load_registered_toolsets(self, package_name, tools_to_load, tools_manager=None):
        self._load_registered_paths_toolsets(package_name=package_name)
        self._load_package_toolsets(
            package_name=package_name, tools_to_load=tools_to_load)

        tools_mgr = tools_manager or tpDcc.ToolsMgr

        for pkg_name, toolset_data in self._manager.plugins.items():
            if package_name != pkg_name:
                continue
            if package_name not in self._toolsets:
                self._toolsets[package_name] = list()
            for tool_set in toolset_data.values():
                if tool_set.ID not in self._toolsets[package_name]:
                    toolset_config = tools_mgr().get_tool_config(tool_set.ID, package_name=package_name)
                    if not toolset_config:
                        tpDcc.logger.warning(
                            'No valid configuration file found for toolset: "{}" in package: "{}"'.format(
                                tool_set.ID, package_name))
                        continue
                    tool_set.CONFIG = toolset_config
                    self._toolsets[package_name].append({tool_set.ID: tool_set})

        return True

    def toolset(self, toolset_id, package_name=None, as_dict=False):
        """
        Returns toolset based on its ID
        :param toolset_id: str
        :param package_name: str
        :param as_dict: bool
        :return: ToolsetWidget
        """

        if not package_name:
            package_name = toolset_id.replace('.', '-').split('-')[0]

        package_toolsets = self._toolsets.get(package_name)
        if not package_toolsets:
            tpDcc.logger.warning('No toolsets found in package: {}!'.format(package_name))
            return None

        toolset_found = None
        for package_toolset in package_toolsets:
            if toolset_id in package_toolset:
                toolset_found = package_toolset
                break

        if not toolset_found:
            raise KeyError('"Toolset "{}" not found in package: "{}".'.format(toolset_id, package_name))

        if as_dict:
            return toolset_found
        else:
            return toolset_found[toolset_id]

    def toolset_ids(self, group_type, package_name=None):
        """
        Returns all toolsets in a given group type
        :param group_type: str
        :param package_name: str
        :return: list
        """

        if not self._toolset_groups:
            return None
        if package_name and package_name not in self._toolset_groups:
            return None

        toolsets_found = list()
        for pkg_name, toolset_groups in self._toolset_groups.items():
            for toolset_group in toolset_groups:
                if package_name and package_name != pkg_name:
                    continue
                if toolset_group['type'] == group_type:
                    toolsets_found.extend(toolset_group['toolsets'])

        return list(set(toolsets_found))

    def toolsets(self, group_type, package_name=None, as_dict=False):
        """
        Returns all toolsets available in a given group type
        :param group_type: str
        :param package_name: str
        :param as_dict: bool
        :return: list(ToolsetWidget)
        """

        toolset_ids = self.toolset_ids(group_type, package_name=package_name)
        return [self.toolset(toolset_id, package_name=package_name, as_dict=as_dict) for toolset_id in toolset_ids]

    def toolset_widgets(self, package_name=None, sort=True):
        """
        Returns a list with toolset widgets
        :param package_name: str
        :param sort: bool
        :return:
        """

        tolset_widgets = list()

        if package_name and package_name not in self._toolsets:
            return

        if package_name:
            tolset_widgets = self._toolsets[package_name].values()
        else:
            for package_name, toolsets in self._toolsets.items():
                for toolset in toolsets:
                    for toolset_id, toolset_widget in toolset.items():
                        tolset_widgets.append(toolset_widget)

        if sort:
            tolset_widgets.sort(key=lambda toolset: toolset.CONFIG.get('name'))

        return tolset_widgets

    def toolset_color(self, toolset_id, package_name=None):
        """
        Returns the color of the toolset and shifts it if necessary
        :param toolset_id: str
        :param package_name: str
        :return: tuple(float, float, float)
        """

        if not toolset_id:
            return 255, 255, 255

        if not package_name:
            package_name = toolset_id.replace('.', '-').split('-')[0]

        if self._toolset_groups and package_name in self._toolset_groups:
            for pkg_name, toolset_groups in self._toolset_groups.items():
                if package_name != pkg_name:
                    continue
                for toolset_group in toolset_groups:
                    if toolset_id in toolset_group['toolsets']:
                        index = toolset_group['toolsets'].index(toolset_id)
                        group_color = tuple(toolset_group['color'])
                        hue_shift = toolset_group['hue_shift'] * (index + 1)
                        return tuple(color.hue_shift(group_color, hue_shift))
        else:
            tpDcc.logger.warning(
                'ToolSet "{}" not found in any toolset group. Impossible to retrieve color!'.format(toolset_id))
            return 255, 255, 255

    def group_types(self):
        found_group_types = list()
        for pkg_name, toolset_groups in self._toolset_groups.items():
            for toolset_group in toolset_groups:
                found_group_types.append(toolset_group['name'])

        return found_group_types

    def group_type(self, group_name):
        """
        Returns type by group name
        :param group_name: str
        :return: str
        """

        for pkg_name, toolset_groups in self._toolset_groups.items():
            for toolset_group in toolset_groups:
                if toolset_group['name'] == group_name:
                    return toolset_group['type']

        return None

    def group_color(self, group_type, package_name=None):
        """
        Returns color by group type
        :param group_type: str
        :return: str
        """

        if not self._toolset_groups:
            return

        for pkg_name, toolset_groups in self._toolset_groups.items():
            if package_name and pkg_name != package_name:
                continue
            for toolset_group in toolset_groups:
                if toolset_group['type'] == group_type:
                    return toolset_group['color']

        return None

    def group_from_toolset(self, toolset_id, package_name=None):
        """
        Returns group of given toolset
        :param toolset_id: str
        :param package_name: str
        :return: str
        """

        if not self._toolset_groups:
            return

        for pkg_name, toolset_groups in self._toolset_groups.items():
            if package_name and pkg_name != package_name:
                continue
            for toolset_group in toolset_groups:
                for tool_set in toolset_group['toolsets']:
                    if tool_set == toolset_id:
                        return toolset_group['type']

        return None

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _load_registered_paths_toolsets(self, package_name):
        """
        Loads all toolsets found in registered paths
        """

        if not self._registered_paths:
            return

        # Load toolsets data
        for pkg_name, registered_paths in self._registered_paths.items():
            if package_name != pkg_name:
                continue
            for registered_path in registered_paths:
                if not registered_path or not os.path.isdir(registered_path):
                    continue
                for pth in folder.get_files_with_extension(
                        toolset.ToolsetWidget.EXTENSION, registered_path, full_path=True, recursive=True):
                    try:
                        toolset_data = yamlio.read_file(pth, maintain_order=True)
                    except Exception:
                        tpDcc.logger.warning('Impossible to read toolset data from: "{}!'.format(pth))
                        continue
                    if pkg_name not in self._toolset_groups:
                        self._toolset_groups[pkg_name] = list()
                    toolset_type = toolset_data.get('type')
                    toolset_not_added = True
                    for _, toolset_groups in self._toolset_groups.items():
                        for toolset_group in toolset_groups:
                            if toolset_type == toolset_group['type']:
                                toolset_not_added = False
                                break
                        if not toolset_not_added:
                            break
                    if toolset_not_added:
                        self._toolset_groups[pkg_name].append(toolset_data)

        # Load toolsets widgets
        for pkg_name, registered_paths in self._registered_paths.items():
            if package_name != pkg_name:
                continue
            self._manager.register_paths(registered_paths, package_name=pkg_name)

    def _load_package_toolsets(self, package_name, tools_to_load):
        """
        Loads all toolsets available in given package
        :param package_name: str
        :param tools_to_load: lsit
        :param dev: bool
        """

        if not tools_to_load:
            return
        tools_to_load = python.force_list(tools_to_load)

        paths_to_register = OrderedDict()

        tools_path = '{}.tools.{}'
        tools_paths_to_load = list()
        for tool_name in tools_to_load:
            pkg_path = tools_path.format(package_name, tool_name)
            pkg_loader = loader.find_loader(pkg_path)
            if not pkg_loader:
                continue
            if tool_name not in paths_to_register:
                paths_to_register[tool_name] = list()

            package_filename = pkg_loader.filename if python.is_python2() else os.path.dirname(pkg_loader.path)
            if package_filename not in tools_paths_to_load:
                tools_paths_to_load.append(package_filename)

        # Find toolset widgets are located
        if tools_paths_to_load:
            self._manager.register_paths(tools_paths_to_load, package_name=package_name)


@decorators.Singleton
class ToolsetsManagerSingleton(ToolsetsManager, object):
    """
    Singleton class that holds preferences manager instance
    """

    def __init__(self):
        ToolsetsManager.__init__(self)
