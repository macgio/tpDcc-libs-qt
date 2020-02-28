#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create different kind of labels
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import graphicseffects


class DragDropLine(QLineEdit, object):
    """
    QLineEdit that supports drag and drop behaviour
    """

    def __init__(self, parent=None):
        super(DragDropLine, self).__init__(parent)

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


class ClickLabel(QLabel, object):
    """
    This label emits a clicked signal when the user clicks on it
    """

    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super(ClickLabel, self).mousePressEvent(event)


class RightElidedLabel(QLabel, object):
    """
    Custom label which supports elide right
    """

    def __init__(self, *args):
        super(RightElidedLabel, self).__init__(*args)
        self._text = ''

    def setText(self, text):
        """
        Overrides base QLabel setText function
        Used to store original text
        :param text: str
        """

        self._text = text
        super(RightElidedLabel, self).setText(text)

    def resizeEvent(self, event):
        """
        Overrides base QLabel resizeEvent function
        Modifies the text with elided text
        :param event: QResizeEvent
        """

        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._text, Qt.ElideRight, self.width())
        super(RightElidedLabel, self).setText(elided)


class ElidedLabel(QLabel, object):
    """
    This label elides text and adds ellipses if the text does not fit
    properly withing the widget frame
    """

    def __init__(self, parent=None):
        super(ElidedLabel, self).__init__(parent=parent)

        self._elide_mode = Qt.ElideRight
        self._actual_text = ""
        self._line_width = 0
        self._ideal_width = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def sizeHint(self):

        base_size_hint = super(ElidedLabel, self).sizeHint()
        return QSize(self._get_width_hint(), base_size_hint.height())

    def _get_width_hint(self):

        if not self._ideal_width:

            doc = QTextDocument()
            try:
                # add the extra space to buffer the width a bit
                doc.setHtml(self._actual_text + "&nbsp;")
                doc.setDefaultFont(self.font())
                width = doc.idealWidth()
            except Exception:
                width = self.width()
            finally:
                qtutils.safe_delete_later(doc)

            self._ideal_width = width

        return self._ideal_width

    def _get_elide_mode(self):
        """
        Returns current elide mode
        """

        return self._elide_mode

    def _set_elide_mode(self, value):
        """
        Set the current elide mode.
        """

        if value != Qt.ElideLeft and value != Qt.ElideRight:
            raise ValueError("elide_mode must be set to either QtCore.Qt.ElideLeft or QtCore.Qt.ElideRight")
        self._elide_mode = value
        self._update_elided_text()

    elide_mode = property(_get_elide_mode, _set_elide_mode)

    def text(self):
        """
        Overridden base method to return the original unmodified text
        """
        return self._actual_text

    def setText(self, text):
        """
        Overridden base method to set the text on the label
        """
        # clear out the ideal width so that the widget can recalculate based on
        # the new text
        self._ideal_width = None
        self._actual_text = text
        self._update_elided_text()

        # if we're elided, make the tooltip show the full text
        if super(ElidedLabel, self).text() != self._actual_text:
            # wrap the actual text in a paragraph so that it wraps nicely
            self.setToolTip("<p>%s</p>" % (self._actual_text,))
        else:
            self.setToolTip("")

    def resizeEvent(self, event):
        """
        Overridden base method called when the widget is resized.
        """

        self._update_elided_text()

    def _update_elided_text(self):
        """
        Update the elided text on the label
        """

        text = self._elide_text(self._actual_text, self._elide_mode)
        QLabel.setText(self, text)

    def _elide_text(self, text, elide_mode):
        """
        Elide the specified text using the specified mode
        :param text:        The text to elide
        :param elide_mode:  The elide mode to use
        :returns:           The elided text.
        """

        # target width is the label width:
        target_width = self.width()

        # Use a QTextDocument to measure html/richtext width
        doc = QTextDocument()
        try:
            doc.setHtml(text)
            doc.setDefaultFont(self.font())

            # if line width is already less than the target width then great!
            line_width = doc.idealWidth()
            if line_width <= target_width:
                self._line_width = line_width
                return text

            # depending on the elide mode, insert ellipses in the correct place
            cursor = QTextCursor(doc)
            ellipses = ""
            if elide_mode != Qt.ElideNone:
                # add the ellipses in the correct place:
                ellipses = "..."
                if elide_mode == Qt.ElideLeft:
                    cursor.setPosition(0)
                elif elide_mode == Qt.ElideRight:
                    char_count = doc.characterCount()
                    cursor.setPosition(char_count - 1)
                cursor.insertText(ellipses)
            ellipses_len = len(ellipses)

            # remove characters until the text fits within the target width:
            while line_width > target_width:

                start_line_width = line_width

                # if string is less than the ellipses length then just return
                # an empty string
                char_count = doc.characterCount()
                if char_count <= ellipses_len:
                    self._line_width = 0
                    return ""

                # calculate the number of characters to remove - should always remove at least 1
                # to be sure the text gets shorter!
                line_width = doc.idealWidth()
                p = target_width / line_width
                # play it safe and remove a couple less than the calculated amount
                chars_to_delete = max(1, char_count - int(float(char_count) * p) - 2)

                # remove the characters:
                if elide_mode == Qt.ElideLeft:
                    start = ellipses_len
                    end = chars_to_delete + ellipses_len
                else:
                    # default is to elide right
                    start = max(0, char_count - chars_to_delete - ellipses_len - 1)
                    end = max(0, char_count - ellipses_len - 1)

                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()

                # update line width:
                line_width = doc.idealWidth()

                if line_width == start_line_width:
                    break

            self._line_width = line_width
            return doc.toHtml()
        finally:
            qtutils.safe_delete_later(doc)

    @property
    def line_width(self):
        """
        :returns: int, width of the line of text in pixels
        """
        return self._line_width


class ThumbnailLabel(QLabel, object):
    def __init__(self, parent=None):
        super(ThumbnailLabel, self).__init__(parent=parent)

    def setPixmap(self, pixmap):
        if pixmap.height() > 55 or pixmap.width() > 80:
            pixmap = pixmap.scaled(QSize(80, 55), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super(ThumbnailLabel, self).setPixmap(pixmap)


class AnimatedLabel(QLabel, object):
    def __init__(self, text='', duration=800, parent=None):
        super(AnimatedLabel, self).__init__(text, parent=parent)

        font = self.font()
        font.setPointSize(18)
        font.setBold(True)
        self.setFont(font)

        self.opacity_effect = graphicseffects.OpacityEffect(target=self, duration=duration)

        self.opacity_effect.animation.valueChanged.connect(self._set_label_opacity)
        self.opacity_effect.animation.finished.connect(self.hide)

    # region Properties
    def get_duration(self):
        return self.opacity_effect.duration

    def set_duration(self, value):
        self.opacity_effect.duration = value

    duration = property(get_duration, set_duration)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self.opacity_effect.animation.currentValue())
        if self.text():
            painter.drawText(event.rect(), self.text())

    def show_message(self, text):
        self.setText(text)
        parent = self.parent()
        if parent:
            # TODO: Add option to set aligment of the text inside its parent
            self.move(10, parent.size().height() - self.fontMetrics().height() - 10)
            # if isinstance(parent, QAbstractScrollArea) and parent.verticalScrollBar().isVisible():
            #     self.move(
            #     parent.size().width() - self.fontMetrics().width(text) - 10 - parent.verticalScrollBar().width(), 0)
            # else:
            #     self.move(parent.size().width() - self.fontMetrics().width(text) - 10, 0)
        self.opacity_effect.fade_in_out()

    def _set_label_opacity(self, value):
        if self.opacity_effect.animation.state() == QPropertyAnimation.Running:
            self.setVisible(value > 0)
            self.update()


class IconLabel(QLabel, object):
    """
    Displays an icon beside a standard label
    """

    clicked = Signal()

    def __init__(self, *args, **kwargs):
        self._icon = kwargs.pop('icon') if 'icon' in kwargs else None
        self._press = False
        self._two_sided = True

        super(IconLabel, self).__init__(*args, **kwargs)

        self.setContentsMargins(20, 0, 0, 0)
        self._value_a = self.text()
        self._value_b = self.text()

    def get_value_a(self):
        return self._value_a

    def get_value_b(self):
        return self._value_b

    value_a = property(get_value_a)
    value_b = property(get_value_b)

    def mousePressEvent(self, event):
        if self._two_sided:
            self._press = True
            self.setText(self._value_a, False)
            self.update()
        self.clicked.emit()

    def mouseReleaseEvent(self, event):
        if self._two_sided:
            self._press = False
            self.setText(self._value_b, False)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if self._icon:
            self._icon.paint(p, QRect(0, self.height() * 0.5 - 5, 12, 12))
        super(IconLabel, self).paintEvent(event)

    def setText(self, text, update=True):
        super(IconLabel, self).setText('<font>%s</font>' % text)
        if update:
            self._value_b = text

    def set_icon(self, icon):
        self._icon = icon


class ClippedLabel(QLabel, object):
    def __init__(self, text='', width=0, ellipsis=True, always_show_all=False, parent=None):
        super(ClippedLabel, self).__init__(text, parent)

        self._always_show_all = always_show_all
        self._ellipsis = ellipsis

        self._width = None
        self._text = None
        self._elided = None

        self.setMinimumWidth(width if width else 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.drawFrame(painter)
        margin = self.margin()
        rect = self.contentsRect()
        rect.adjust(margin, margin, -margin, -margin)
        text = self.text()
        width = rect.width()
        if text != self._text or width != self._width:
            self._text = text
            self._width = width
            self._elided = self.fontMetrics().elidedText(text, Qt.ElideRight, width)
        option = QStyleOption()
        option.initFrom(self)

        if self._always_show_all:
            if self._width >= self.sizeHint().width():
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette, self.isEnabled(),
                    self.text(), self.foregroundRole())
        else:
            if self._ellipsis:
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette, self.isEnabled(),
                    self._elided, self.foregroundRole())
            else:
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette, self.isEnabled(),
                    self.text(), self.foregroundRole())
