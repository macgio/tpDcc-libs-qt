#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with images
"""

from __future__ import print_function, division, absolute_import

import os
import re
import base64

from Qt.QtCore import *
from Qt.QtGui import *

import tpQtLib


class ImageWorker(QRunnable, object):
    """
    Class that loads an image in a thread
    """

    class ImageWorkerSignals(QObject, object):
        triggered = Signal(object)

    def __init__(self, *args):
        super(ImageWorker, self).__init__(*args)

        self._path = None
        self.signals = ImageWorker.ImageWorkerSignals()

    def set_path(self, path):
        """
        Set the image path to be loaded
        :param path: str
        """

        self._path = path

    def run(self):
        """
        Overrides base QRunnable run function
        This is the starting point for the thread
        """

        try:
            if self._path:
                image = QImage(str(self._path))
                self.signals.triggered.emit(image)
        except Exception as e:
            tpQtLib.logger.error('Cannot load thumbnail image!')


class ImageSequence(QObject, object):

    DEFAULT_FPS = 24

    frameChanged = Signal(int)

    def __init__(self, path, *args):
        super(ImageSequence, self).__init__(*args)

        self._fps = self.DEFAULT_FPS
        self._timer = None
        self._frame = 0
        self._frames = list()
        self._dirname = None
        self._paused = False

        if path:
            self.set_dirname(path)

    def set_path(self, path):
        """
        Set as singal frame image sequence
        :param path: str
        """

        self._frame = 0
        self._frames = [path]

    def dirname(self):
        """
        Return the location to the image sequence in disk
        :return: str
        """

        return self._dirname

    def set_dirname(self, dirname):
        """
        Set the location where image sequence files are located
        :param dirname: str
        """

        def natural_sort_items(items):
            """
            Sort the given list in the expected way
            :param items: list(str)
            """

            convert = lambda text: int(text) if text.isdigit() else text
            alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
            items.sort(key=alphanum_key)

        self._dirname = dirname
        if os.path.isdir(dirname):
            self._frames = [dirname + '/' + filename for filename in os.listdir(dirname)]
            natural_sort_items(self._frames)

    def start(self):
        """
        Starts the image sequence
        """

        self.reset()
        if self._timer:
            self._timer.start(1000.0 / self._fps)

    def pause(self):
        """
        Pause image sequence
        """

        self._paused = True
        self._timer.stop()

    def resume(self):
        """
        Play image sequence after Pause
        """

        if self._paused:
            self._paused = False
            self._timer.start()

    def stop(self):
        """
        Stop the image sequence
        """

        self._timer.stop()

    def reset(self):
        """
        Stop and reset the current frame to 0
        """

        if not self._timer:
            self._timer = QTimer(self.parent())
            self._timer.setSingleShot(False)
            self._timer.timeout.connect(self._on_frame_changed)

        if not self._paused:
            self._frame = 0
        self._timer.stop()

    def frames(self):
        """
        Return all the filenames in the image sequence
        :return: list(str)
        """

        return self._frames

    def percent(self):
        """
        Return the current frame position as a percentage
        :return: float
        """

        if len(self._frames) == self._frame + 1:
            _percent = 1
        else:
            _percent = float((len(self._frames) + self._frame)) / len(self._frames) - 1

        return _percent

    def frame_count(self):
        """
        Returns the number of frames
        :return: int
        """

        return len(self._frames)

    def current_frame_number(self):
        """
        Returns the current frame
        :return: int
        """

        return self._frame

    def current_filename(self):
        """
        Returns the current file name
        :return: str
        """

        try:
            return self._frames[self.current_frame_number()]
        except IndexError:
            pass

    def current_icon(self):
        """
        Returns the current frames as QIcon
        :return: QIcon
        """

        return QIcon(self.current_filename())

    def current_pixmap(self):
        """
        Returns the current frame as QPixmap
        :return: QPixmap
        """

        return QPixmap(self.current_filename())

    def jump_to_frame(self, frame):
        """
        Set the current frame
        :param frame: int
        """

        if frame >= self.frame_count():
            frame = 0
        self._frame = frame
        self.frameChanged.emit(frame)

    def _on_frame_changed(self):
        """
        Internal callback function that is called when the current frame changes
        """

        if not self._frames:
            return

        frame = self._frame
        frame += 1
        self.jump_to_frame(frame)


# region Public Functions
def image_to_base64(image_path):
    """
    Converts image file to base64
    :param image_path: str
    :return: str
    """

    if os.path.isfile(image_path):
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read())


def base64_to_image(base64_string, image_format='PNG'):
    """
    Converts base64 to QImage
    :param base64_string: str
    :param image_format: str
    :return: QImage
    """

    if isinstance(base64_string, basestring):
        ba = QByteArray.fromBase64(base64_string)
        image = QImage.fromData(ba, image_format)
        return image


def base64_to_bitmap(base64_string, bitmap_format='PNG'):
    """
    Converts base64 to QBitmap
    :param base64_string: str
    :param image_format: str
    :return: QBitmap
    """

    if isinstance(base64_string, basestring):
        image = base64_to_image(base64_string, bitmap_format)
        if image is not None:
            bitmap = QBitmap.fromImage(image)
            return bitmap


def base64_to_icon(base64_string, icon_format='PNG'):
    """
    Converts base64 to QIcon
    :param base64_string: str
    :param icon_format: str
    :return: QIcon
    """

    if isinstance(base64_string, basestring):
        bitmap = base64_to_bitmap (base64_string, icon_format)
        if bitmap is not None:
            icon = QIcon(bitmap)
            return icon
# endregion
