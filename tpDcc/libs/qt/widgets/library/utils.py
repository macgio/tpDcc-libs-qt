#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions used by libraries
"""

from __future__ import print_function, division, absolute_import

import os
import abc
import json
import time
import shutil
import locale
import getpass
import logging
from copy import deepcopy
from collections import OrderedDict, Mapping

import six

from tpDcc.libs.python import python, decorators, fileio, path as path_utils

import tpDcc as tp
from tpDcc.libs import qt
from tpDcc.libs.qt.widgets.library import exceptions

if tp.is_maya():
    from tpDcc.dccs.maya.core import decorators as maya_decorators
    show_wait_cursor_decorator = maya_decorators.show_wait_cursor
else:
    show_wait_cursor_decorator = decorators.empty_decorator

LOGGER = logging.getLogger()


class Node(object):

    @classmethod
    def ls(cls, objects=None, selection=False):
        if objects is None and not selection:
            objects = tp.Dcc.all_scene_objects(full_path=False)
        else:
            objects = objects or list()
            if selection:
                objects.extend(tp.Dcc.selected_nodes(full_path=False) or [])

        return [cls(name) for name in objects]

    def __init__(self, name, attributes=None):
        try:
            self._name = name.encode('ascii')
        except UnicodeEncodeError:
            raise UnicodeEncodeError('Not a valid ASCII name "{}".'.format(name))

        self._short_name = None
        self._namespace = None
        self._mirror_axis = None
        self._attributes = attributes

    def __str__(self):
        return self.name()

    def name(self):
        return self._name

    def attributes(self):
        return self._attributes

    def short_name(self):
        if self._short_name is None:
            self._short_name = self.name().split('|')[-1]
        return self._short_name

    def to_short_name(self):
        names = tp.Dcc.list_nodes(node_name=self.short_name())
        if len(names) == 1:
            return Node(names[0])
        elif len(names) > 1:
            raise exceptions.MoreThanOneObjectFoundError('More than one object found {}'.format(str(names)))
        else:
            raise exceptions.NoObjectFoundError('No object found {}'.format(self.short_name()))

    def namespace(self):
        if self._namespace is None:
            self._namespace = ':'.join(self.short_name().split(':')[:-1])
        return self._namespace

    def strip_first_pipe(self):
        if self.name().startswith('|'):
            self._name = self.name()[1:]

    def exists(self):
        return tp.Dcc.object_exists(self.name())

    def is_long(self):
        return '|' in self.name()

    def is_referenced(self):
        return tp.Dcc.node_is_referenced(self.name())

    def set_mirror_axis(self, mirror_axis):
        """
        Sets node mirror axis
        :param mirror_axis: list(int)
        """

        self._mirror_axis = mirror_axis

    def set_namespace(self, namespace):
        """
        Sets namespace for current node
        :param namespace: str
        """

        new_name = self.name()
        old_name = self.name()

        new_namespace = namespace
        old_namespace = self.namespace()

        if new_namespace == old_namespace:
            return self.name()

        if old_namespace and new_namespace:
            new_name = old_name.replace(old_namespace + ":", new_namespace + ":")
        elif old_namespace and not new_namespace:
            new_name = old_name.replace(old_namespace + ":", "")
        elif not old_namespace and new_namespace:
            new_name = old_name.replace("|", "|" + new_namespace + ":")
            if new_namespace and not new_name.startswith("|"):
                new_name = new_namespace + ":" + new_name

        self._name = new_name

        self._short_name = None
        self._namespace = None

        return self.name()


class TransferObject(object):

    DEFAULT_DATA = {'metadata': {}, 'objects': {}}

    @classmethod
    def from_path(cls, path, force_creation=False):
        """
        Returns a new transfer instance for the given path
        :param path: str
        :param force_creation: bool
        :return: TransferObject
        """

        t = cls()
        t.set_path(path)

        if not os.path.isfile(path) or force_creation:
            filename = os.path.basename(path)
            filedir = os.path.dirname(path)
            if not os.path.isdir(filedir):
                os.makedirs(filedir)
            fileio.create_file(filename, filedir)

        t.read()

        return t

    @classmethod
    def from_objects(cls, objects, **kwargs):
        """
        Returns a new transfer instance for the given objects
        :param objects: list(str)
        :param kwargs: dict
        :return: TransferObject
        """

        t = cls(**kwargs)
        for obj in objects:
            t.add(obj)

        return t

    @staticmethod
    def read_json(path):
        """
        Reads the given JSON path
        :param path: str
        :return: dict
        """

        with open(path, 'r') as f:
            data = f.read() or '{}'

        data = json.loads(data)

        return data

    def __init__(self):
        self._path = None
        self._namespaces = None
        self._data = deepcopy(self.DEFAULT_DATA)

    @abc.abstractmethod
    def load(self, *args, **kwargs):
        pass

    def path(self):
        """
        Returns the disk location for the transfer object
        :return: str
        """

        return self._path

    def set_path(self, path):
        """
        Set the disk location for loading and saving the transfer object
        :param path: str
        """

        self._path = path

    def validate(self, **kwargs):
        """
        Validates the given keyword arguments for the current IO object
        :param kwargs: dict
        """

        namespaces = kwargs.get('namespaces')
        if namespaces is not None:
            scene_namespaces = tp.Dcc.scene_namespaces()
            for namespace in namespaces:
                if namespace and namespace not in scene_namespaces:
                    msg = 'The namespace "{}" does not exists in the scene! ' \
                          'Please choose a namespace which exists.'.format(namespace)
                    raise ValueError(msg)

    def mtime(self):
        """
        Returns the modification datetime of file path
        :return: str
        """

        return os.path.getmtime(self.path())

    def ctime(self):
        """
        Returns the creation datetime of file path
        :return: str
        """

        return os.path.getctime(self.path())

    def data(self):
        """
        Returns all the data for the transfer object
        :return: dict
        """

        return self._data

    def set_data(self, data):
        """
        Sets the data for the transfer object
        :param data: dict
        """

        if not data:
            self._data = self.DEFAULT_DATA
        else:
            self._data = data

    def objects(self):
        """
        Returns all the object data
        :return: dict
        """

        return self.data().get('objects', {})

    def object(self, name):
        """
        Returns the data for the given object name
        :param name: str
        :return: dict
        """

        return self.objects().get(name, {})

    def create_object_data(self, name):
        """
        Creates the object data for the given object name
        :param name: str
        :return: dict
        """

        return dict()

    def namespaces(self):
        """
        Returns the namespaces contained in the transfer object
        :return: list(str)
        """

        if self._namespaces is None:
            group = group_objects(self.objects())
            self._namespaces = group.keys()

        return self._namespaces

    def count(self):
        """
        Returns the number of objects in the transfer object
        :return: int
        """

        return len(self.objects() or list())

    def add(self, objects):
        """
        Adds the given objects to the transfer object
        :param objects: str or list(str)
        """

        objects = python.force_list(objects)

        for name in objects:
            self.objects()[name] = self.create_object_data(name)

    def remove(self, objects):
        """
        Removes the given objecst from the transfer object
        :param objects: str or list(str)
        """

        objects = python.force_list(objects)

        for obj in objects:
            del self.objects()[obj]

    def metadata(self):
        """
        Returns the current metadata for the transfer object
        :return: dict
        """

        return self.data().get('metadata', dict())

    def set_metadata(self, key, value):
        """
        Sets the given key and value in the metadata
        :param key: str
        :param value: int or str or float or dict
        """

        self.data()['metadata'][key] = value

    def update_metadata(self, metadata):
        """
        Updates the given key and value in the metadata
        :param metadata:dict
        """

        self.data()['metadata'].update(metadata)

    def read(self, path=''):
        """
        Returns the data from the path set on the Transfer Object
        :param path: str
        :return: dict
        """

        path = path or self.path()
        data = self.read_json(path)
        self.set_data(data)

    def dump(self, data=None):
        """
        Dumps JSON info
        :param data: str or dict
        """

        if data is None:
            data = self.data()

        return json.dumps(data, indent=2)

    def data_to_save(self):
        """
        Returns data to save
        Can be override to store custom data
        :return: dict
        """

        encoding = locale.getpreferredencoding()
        user = getpass.getuser()
        if user:
            user = user.decode(encoding)

        ctime = str(time.time()).split('.')[0]
        references = get_reference_data(self.objects())

        self.set_metadata('user', user)
        self.set_metadata('ctime', ctime)
        self.set_metadata('references', references)
        self.set_metadata('mayaVersion', str(tp.Dcc.get_version())),
        self.set_metadata('mayaSceneFile', tp.Dcc.scene_name())

        metadata = {'metadata': self.metadata()}
        data = self.dump(metadata)[:-1] + ','

        objects = {'objects': self.objects()}
        data += self.dump(objects)[1:]

        return data

    @show_wait_cursor_decorator
    def save(self, path=None):
        """
        Saves the current metadata ond object data to the given path
        :param path: str
        """

        qt.logger.info('Saving object: {}'.format(path))

        data = self.data_to_save()

        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(path, 'w') as f:
            f.write(str(data))

        qt.logger.debug('Saved object: {}'.format(path))


def absolute_path(data, start):
    """
    Returns an absolute version of all the paths in data using the start path
    :param data: str
    :param start: str
    :return: str
    """

    rel_path1 = path_utils.normalize_path(os.path.dirname(start))
    rel_path2 = path_utils.normalize_path(os.path.dirname(rel_path1))
    rel_path3 = path_utils.normalize_path(os.path.dirname(rel_path2))

    if not rel_path1.endswith("/"):
        rel_path1 += "/"

    if not rel_path2.endswith("/"):
        rel_path2 += "/"

    if not rel_path3.endswith("/"):
        rel_path3 += "/"

    data = data.replace('../../../', rel_path3)
    data = data.replace('../../', rel_path2)
    data = data.replace('../', rel_path1)

    return data


def update(data, other):
    """
    Update teh value of a nested dictionary of varying depth
    :param data: dict
    :param other: dict
    :return: dict
    """

    for key, value in other.items():
        if isinstance(value, Mapping):
            data[key] = update(data.get(key, {}), value)
        else:
            data[key] = value

    return data


def read(path):
    """
    Returns the contents of the given file
    :param path: str
    :return: str
    """

    data = ''
    path = path_utils.normalize_path(path)
    if os.path.isfile(path):
        with open(path) as f:
            data = f.read() or data
    data = absolute_path(data, path)

    return data


def write(path, data):
    """
    Writes the given data to the given file on disk
    :param path: str
    :param data: str
    """

    path = path_utils.normalize_path(path)
    data = path_utils.get_relative_path(data, path)

    tmp = path + '.tmp'
    bak = path + '.bak'

    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if os.path.exists(tmp):
        msg = 'The path is locked for writing and cannot be accessed {}'.format(tmp)
        raise IOError(msg)

    try:
        with open(tmp, 'w') as f:
            f.write(data)
            f.flush()

        if os.path.exists(bak):
            os.remove(bak)
        if os.path.exists(path):
            os.rename(path, bak)
        if os.path.exists(tmp):
            os.rename(tmp, path)
        if os.path.exists(path) and os.path.exists(bak):
            os.remove(bak)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        if not os.path.exists(path) and os.path.exists(bak):
            os.rename(bak, path)

        raise


def update_json(path, data):
    """
    Update a JSON file with the given data
    :param path: str
    :param data: dict
    """

    data_ = read_json(path)
    data_ = update(data_, data)
    save_json(path, data_)


def read_json(path):
    """
    Reads the given JSON file and deserialize it to a Python object
    :param path: str
    :return: dict
    """

    path = path_utils.normalize_path(path)
    data = read(path) or '{}'
    data = json.loads(data)

    return data


def save_json(path, data):
    """
    Serialize given tdata to a JSON string and write it to the given path
    :param path: str
    :param data: dict
    """

    path = path_utils.normalize_path(path)
    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
    data = json.dumps(data, indent=4)
    write(path, data)


def replace_json(path, old, new, count=-1):
    """
    Repalces the old value with the new value in the given JSON file
    :param path: str
    :param old: str
    :param new: str
    :param count: int
    :return: dict
    """

    old = old.encode("unicode_escape")
    new = new.encode("unicode_escape")

    data = read(path) or "{}"
    data = data.replace(old, new, count)
    data = json.loads(data)

    save_json(path, data)

    return data


def generate_unique_path(path, max_attempts=1000):
    """
    Generates a unique path on disk
    :param path: str
    :param max_attempts: int
    :return: str
    """

    attempt = 1
    dirname, name, extension = path_utils.split_path(path)
    path_ = '{dirname}/{name} ({number}){extension}'

    while os.path.exists(path):
        attempt += 1
        path = path_.format(name=name, number=attempt, dirname=dirname, extension=extension)
        if attempt >= max_attempts:
            raise ValueError('Cannot generate unique name for path {}'.format(path))

    return path


def rename_path_in_file(path, source, target):
    """
    Renames the given source path to the given target path
    :param path: str
    :param source: str
    :param target: str
    """

    source = path_utils.normalize_path(source)
    target = path_utils.normalize_path(target)

    source1 = '"' + source + '"'
    target1 = '"' + target + '"'

    replace_json(path, source1, target1)

    source2 = '"' + source
    target2 = '"' + target

    if not source2.endswith("/"):
        source2 += "/"

    if not target2.endswith("/"):
        target2 += "/"

    replace_json(path, source2, target2)


def rename_path(source, target, extension=None, force=False):
    """
    Renames the given source path to the given destination path
    :param source: str
    :param target: str
    :param extension: str
    :param force: bool
    :return: str
    """

    dirname = os.path.dirname(source)

    if '/' not in target:
        target = os.path.join(dirname, target)

    if extension and extension not in target:
        target += extension

    source = path_utils.normalize_path(source)
    target = path_utils.normalize_path(target)
    LOGGER.debug('Renaming: {} > {}'.format(source, target))

    if source == target and not force:
        raise exceptions.RenamePathError('The source path and destination path are the same: {}'.format(source))
    if os.path.exists(target) and not force:
        raise exceptions.RenamePathError('Cannot save over an existing path: "{}"'.format(target))
    if not os.path.exists(dirname):
        raise exceptions.RenamePathError('The system cannot find the specified path: "{}"'.format(dirname))
    if not os.path.exists(os.path.dirname(target)) and force:
        os.mkdir(os.path.dirname(target))
    if not os.path.exists(source):
        raise exceptions.RenamePathError('The system cannot find the specified path: "{}"'.format(source))

    os.rename(source, target)
    LOGGER.debug('Renamed: {} > {}'.format(source, target))

    return target


def copy_path(source, target):
    """
    Makes a copy of the given source path to the given destination path
    :param source: str
    :param target: str
    :return: str
    """

    dirname = os.path.dirname(source)
    if '/' not in target:
        target = os.path.join(dirname, target)

    source = path_utils.normalize_path(source)
    target = path_utils.normalize_path(target)

    if source == target:
        raise IOError('The source path and destination path are the same: {}'.format(source))
    if os.path.exists(target):
        raise IOError('Cannot copy over an existing path: {}'.format(target))
    if os.path.isfile(source):
        shutil.copy(source, target)
    else:
        shutil.copytree(source, target)

    return target


def move_path(source, target):
    """
    Moves the given source path to the given destination path
    :param source: str
    :param target: str
    :return: str
    """

    source = six.u(source)
    dirname, name, extension = path_utils.split_path(source)
    if not os.path.exists(source):
        raise exceptions.MovePathError('No such file or directory: {}'.format(source))
    if os.path.isdir(source):
        target = '{}/{}{}'.format(target, name, extension)
        target = generate_unique_path(target)
    shutil.move(source, target)

    return target


def move_paths(source_paths, target):
    """
    Moves the given paths to the given destination paths
    :param source_paths: list(str)
    :param target: str
    :return: list(str)
    """

    if not os.path.exists(target):
        os.makedirs(target)

    for source in source_paths or list():
        if not source:
            continue
        basename = os.path.basename(source)
        target_ = path_utils.normalize_path(os.path.join(target, basename))
        LOGGER.debug('Moving Content: {} > {}'.format(source, target_))
        shutil.move(source, target_)


def remove_path(path):
    """
    Removes the given path from disk
    :param path: str
    """

    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def group_objects(objects):
    """
    Group objects as Nodes
    :param objects: list(str)
    :return: dict
    """

    results = dict()
    for name in objects:
        node = Node(name)
        results.setdefault(node.namespace(), list())
        results[node.namespace()].append(name)

    return results


def get_reference_paths(objects, without_copy_number=False):
    """
    Retursn the reference paths for the given objects
    :param objects: list(str)
    :param without_copy_number: bool
    :return: list(str)
    """

    paths = list()
    for obj in objects:
        if tp.Dcc.node_is_referenced(obj):
            paths.append(tp.Dcc.node_reference_path(obj, without_copy_number=without_copy_number))

    return list(set(paths))


def get_reference_data(objects):
    """
    Retruns the reference paths for the given objects
    :param objects: list(str)
    :return: list(dict)
    """

    data = list()
    paths = get_reference_paths(objects)
    for path in paths:
        data.append({
            'filename': path,
            'unresolved': tp.Dcc.node_reference_path(path, without_copy_number=True),
            'namespace': tp.Dcc.node_namespace(path),
            'node': tp.Dcc.node_is_referenced(path)
        })

    return data
