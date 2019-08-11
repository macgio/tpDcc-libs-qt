#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt stack widgets
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *


class SlidingStackedWidget(QStackedWidget, object):
    """
    QStackedWidget width sliding functionality
    """

    animFinished = Signal(int)

    def __init__(self, parent=None, **kwargs):
        super(SlidingStackedWidget, self).__init__(parent)

        self._current_widget = None     # This variable holds the current widget without taking into account if the animation has finished or not
        self._speed = kwargs.pop('speed', 500)
        self._animation_type = kwargs.pop('animation_type', QEasingCurve.OutCubic)
        self._wrap = kwargs.pop('wrap', True)
        self._vertical = kwargs.pop('vertical', False)
        self._active_state = False
        self._blocked_page_list = list()
        self._now = 0
        self._next = 1

    @property
    def current_widget(self):
        return self._current_widget

    def set_speed(self, speed):
        """
        Sets the animation speed of the sliding
        :param speed: int
        """

        self._speed = speed

    def set_animation(self, animation_type):
        """
        Set the curve animation type of the sliding
        :param animation_type: QEasingCurve
        """

        self._animation_type = animation_type

    def set_vertical_mode(self, vertical=True):
        """
        Sets whether the sliding animation is done vertically or horizontally
        :param vertical: bool
        """

        self._vertical = vertical

    def set_wrap(self, wrap):
        """
        Sets whether the page index is restarted when we arrive the last one or not
        :param wrap: bool
        """

        self._wrap = wrap

    def slide_in_next(self):
        """
        Slides into the next widget
        """

        now = self.currentIndex()
        if self._wrap or now < self.count()-1:
            self.slide_in_index(now+1)

    def slide_in_prev(self):
        """
        Slides into the previous widget
        """

        now = self.currentIndex()
        if self._wrap or now > 0:
            self.slide_in_index(now-1)

    def slide_in_index(self, next, force=False):
        """
        Slides to the given widget index
        :param next: int, index of the widget to slide
        """

        now = self.currentIndex()
        if (self._active_state or next == now) and not force:
            return

        self._active_state = True
        width, height = self.frameRect().width() , self.frameRect().height()
        next %= self.count()
        if next > now:
            if self._vertical:
                offset_x, offset_y = 0, height
            else:
                offset_x, offset_y = width, 0
        else:
            if self._vertical:
                offset_x, offset_y = 0, -height
            else:
                offset_x, offset_y = -width, 0
        self.widget(next).setGeometry(0,  0, width, height)
        pnow , pnext = self.widget(now).pos(), self.widget(next).pos()
        self._point_now = pnow

        self.widget(next).move(pnext.x() + offset_x, pnext.y() + offset_y)
        self.widget(next).show()
        self.widget(next).raise_()
        self._current_widget = self.widget(next)

        anim_now = QPropertyAnimation(self.widget(now), 'pos')
        anim_now.setDuration(self._speed)
        anim_now.setStartValue(pnow)
        anim_now.setEndValue(QPoint(pnow.x()-offset_x, pnow.y()-offset_y))
        anim_now.setEasingCurve(self._animation_type)

        anim_next = QPropertyAnimation(self.widget(next), 'pos')
        anim_next.setDuration(self._speed)
        anim_next.setStartValue(QPoint(offset_x+pnext.x(), offset_y+pnext.y()))
        anim_next.setEndValue(pnext)
        anim_next.setEasingCurve(self._animation_type)

        self._anim_group = QParallelAnimationGroup()
        self._anim_group.addAnimation(anim_now)
        self._anim_group.addAnimation(anim_next)
        self._anim_group.finished.connect(self._animation_done_slot)
        self._anim_group.start()

        self._next = next
        self._now = now

    def _animation_done_slot(self):
        self.setCurrentIndex(self._next)
        self.widget(self._now).hide()
        self.widget(self._now).move(self._point_now)
        try:
            self.widget(self._now).update()
        except Exception:
            pass
        self._active_state = False
        self.animFinished.emit(self._next)
