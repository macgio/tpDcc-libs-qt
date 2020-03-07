#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains form widgets for library
"""

from __future__ import print_function, division, absolute_import

import re
import sys
import traceback
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs import qt
from tpDcc.libs.python import decorators
from tpDcc.libs.qt.widgets import label, color


class FormDialog(QFrame, object):

    accepted = Signal(object)
    rejected = Signal(object)

    def __init__(self, parent=None, form=None):
        super(FormDialog, self).__init__(parent)

        self._settings = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self._widgets = list()
        self._validator = None

        self._title = QLabel(self)
        self._title.setObjectName('title')
        self._title.setText('FORM')
        self._description = QLabel(self)
        self._description.setObjectName('description')
        self._form_widget = FormWidget(self)
        self._form_widget.setObjectName('formWidget')
        self._form_widget.validated.connect(self._on_validated)
        btn_layout = QHBoxLayout(self)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        self._accept_btn = QPushButton(self)
        self._accept_btn.setObjectName('acceptButton')
        self._accept_btn.setText('Accept')
        self._accept_btn.clicked.connect(self.accept)
        self._reject_btn = QPushButton(self)
        self._reject_btn.setObjectName('rejectButton')
        self._reject_btn.setText('Cancel')
        self._reject_btn.clicked.connect(self.reject)
        btn_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        btn_layout.addWidget(self._accept_btn)
        btn_layout.addWidget(self._reject_btn)

        self.main_layout.addWidget(self._title)
        self.main_layout.addWidget(self._description)
        self.main_layout.addWidget(self._form_widget)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(btn_layout)

        if form:
            self.set_settings(form)

    def accept_button(self):
        """
        Returns the accept button
        :return: QPushButton
        """

        return self._accept_btn

    def reject_button(self):
        """
        Returns the reject button
        :return: QPushButton
        """

        return self._reject_btn

    def set_settings(self, settings):
        """
        Sets dialog form settings
        :param settings: dict
        """

        self._settings = settings
        title = settings.get("title")
        if title is not None:
            self._title.setText(title)
        callback = settings.get("accepted")
        if not callback:
            self._settings["accepted"] = self._validate_accepted
        callback = settings.get("rejected")
        if not callback:
            self._settings["rejected"] = self._validate_rejected
        description = settings.get("description")
        if description is not None:
            self._description.setText(description)
        validator = settings.get("validator")
        if validator is not None:
            self._form_widget.set_validator(validator)
        layout = settings.get("layout")
        schema = settings.get("schema")
        if schema is not None:
            self._form_widget.set_schema(schema, layout=layout)

    def accept(self):
        """
        Function called when the dialog is accepted
        """

        callback = self._settings.get('accepted')
        if callback:
            callback(**self._form_widget.values())
        self.close()

    def reject(self):
        """
        Function called when the dialog is rejected
        """

        callback = self._settings.get('rejected')
        if callback:
            callback(**self._form_widget.default_values())
        self.close()

    def _validate_accepted(self, **kwargs):
        """
        Internal function called when the accept button has been clicked
        :param kwargs: dict, default values of the form fields
        """

        self._form_widget.validator()(**kwargs)

    def _validate_rejected(self, **kwargs):
        """
        Internal function called when reject button has been clicked
        :param kwargs: dict, default values of the form fields
        """

        self._form_widget.validator()(**kwargs)

    def _on_validated(self):
        """
        Internal callback function that is triggered when the has been validated
        """

        self._accept_btn.setEnabled(not self._form_widget.has_errors())


class FormWidget(QFrame, object):

    accepted = Signal(object)
    stateChanged = Signal()
    validated = Signal()

    def __init__(self, *args, **kwargs):
        super(FormWidget, self).__init__(*args, **kwargs)

        self._schema = list()
        self._widgets = list()
        self._validator = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._options_frame = QFrame(self)
        self._options_frame.setObjectName('optionsFrame')
        options_layout = QVBoxLayout(self._options_frame)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(0)
        self._options_frame.setLayout(options_layout)

        self._title_widget = QPushButton(self)
        self._title_widget.setCheckable(True)
        self._title_widget.setObjectName('titleWidget')
        self._title_widget.toggled.connect(self._on_title_clicked)
        self._title_widget.hide()

        main_layout.addWidget(self._title_widget)
        main_layout.addWidget(self._options_frame)

    def title_widget(self):
        """
        Returns the title widget
        :return: QWidget
        """

        return self._title_widget

    def set_title(self, title):
        """
        Sets the title text
        :param title: str
        """

        self.title_widget().setText(title)

    def is_expanded(self):
        """
        Returns whether the item is expanded or not
        :return: bool
        """

        return self._title_widget.isChecked()

    def set_expanded(self, flag):
        """
        Expands the options if True, otherwise collapses the options
        :param flag: bool
        """

        self._title_widget.blockSignals(True)
        try:
            self._title_widget.setChecked(flag)
            self._options_frame.setVisible(flag)
        finally:
            self._title_widget.blockSignals(False)

    def set_title_visible(self, flag):
        """
        Sets whether the title widget is visible or not
        :param flag: bool
        """

        self.title_widget().setVisible(flag)

    def widget(self, name):
        """
        Returns the widget for the given widget name
        :param name: str
        :return: FieldWidget
        """

        for widget in self._widgets:
            if widget.data().get('name') == name:
                return widget

    def value(self, name):
        """
        Returns the value for the given widget name
        :param name: str
        :return: object
        """

        widget = self.widget(name)
        return widget.value()

    def set_value(self, name, value):
        """
        Sets the value for the given field name
        :param name: str
        :param value: variant
        """

        widget = self.widget(name)
        widget.set_value(value)

    def values(self):
        """
        Returns all the field values indexed by the field name
        :return: dict
        """

        values = dict()
        for widget in self._widgets:
            values[widget.data().get('name')] = widget.value()

        return values

    def default_values(self):
        """
        Returns all teh default field values indexed by the field name
        :return: dict
        """

        values = dict()
        for widget in self._widgets:
            values[widget.data().get('name')] = widget.default()

        return values

    def options(self):
        """
        Returns fields options
        :return: list(dict)
        """

        options = list()
        for widget in self._widgets:
            options.append(widget.data())

        return options

    def state(self):
        """
        Returns the current state
        :return: dict
        """

        options = list()
        for widget in self._widgets:
            options.append(widget.state())

        state = {
            'options': options,
            'expanded': self.is_expanded()
        }

        return state

    def set_state(self, state):
        """
        Sets the current state
        :param state: dict
        """

        expanded = state.get('expanded')
        if expanded is not None:
            self.set_expanded(expanded)

        options = state.get('options')
        if options is not None:
            self._set_state(options)

        self.validate()

    def options_state(self):
        """
        Returns options state
        :return: dict
        """

        state = dict()
        values = self.values()
        options = self.options()
        for option in options:
            name = option.get('name')
            persistent = option.get('persistent')
            if name and persistent:
                state[name] = values[name]

        return state

    def set_state_from_options(self, options):
        """
        Sets state from given options
        :param options: list(dict)
        """

        state = list()
        for option in options:
            state.append({'name': option, 'value': options[option]})

        self._set_state(state)

    def set_schema(self, schema, layout=None):
        """
        Sets the schema for the widget
        :param schema: ilst(dict)
        :param layout: str
        """

        self._schema = schema
        for data in schema:
            cls = FIELD_WIDGET_REGISTRY.get(data.get('type', 'label'))
            if not cls:
                qt.logger.warning('Cannot find widget for {}'.format(data))
                continue
            if layout and not data.get('layout'):
                data['layout'] = layout

            widget = cls(data=data)
            widget.set_data(data)

            value = data.get('value')
            default = data.get('default')
            if value is None and default is not None:
                widget.set_value(default)

            self._widgets.append(widget)

            callback = partial(self._on_option_changed, widget)
            widget.valueChanged.connect(callback)

            self._options_frame.layout().addWidget(widget)

    def validator(self):
        """
        Returns the validator for the form
        :return: fn
        """

        return self._validator

    def set_validator(self, validator):
        """
        Sets the validator for the options
        :param validator: fn
        """

        self._validator = validator

    def reset(self):
        """
        Reset all option widget back to the ir default values
        """

        for widget in self._widgets:
            widget.reset()
        self.validate()

    def validate(self):
        """
        Validates the current options using the validator
        """

        if self._validator:
            fields = self._validator(**self.values())
            if fields:
                self._set_state(fields)
            self.validated.emit()
        else:
            qt.logger.debug('No validator set')

    def has_errors(self):
        """
        Returns whether the form contains any error
        :return: bool
        """

        for widget in self._widgets:
            if widget.data().get('error'):
                return True

        return False

    def _set_state(self, fields):
        """
        Internal function that sets fields state
        :param fields: list(dict)
        """

        for widget in self._widgets:
            widget.blockSignals(True)

        try:
            for widget in self._widgets:
                widget.set_error('')
                for field in fields:
                    if field.get('name') == widget.data().get('name'):
                        widget.set_data(field)
        finally:
            for widget in self._widgets:
                widget.blockSignals(False)

        self.stateChanged.emit()

    def _on_title_clicked(self, toggle):
        """
        Internal callback function that is triggered when the user clicks in the title widget
        """

        self.set_expanded(toggle)
        self.stateChanged.emit()

    def _on_option_changed(self, widget):
        """
        Internal callback function triggered when the given option widget changes its value
        :param widget: FieldWidget
        """

        self.validate()


class FieldWidget(QFrame, object):

    valueChanged = Signal()

    DefaultLayout = 'horizontal'

    def __init__(self, parent=None, data=None):
        super(FieldWidget, self).__init__(parent)

        self._data = data or dict()
        self._error = False
        self._widget = None
        self._default = None
        self._required = None
        self._error_label = None
        self._menu_button = None
        self._action_result = None

        self.setObjectName('fieldWidget')

        direction = self._data.get('layout', self.DefaultLayout)
        if direction == 'vertical':
            main_layout = QVBoxLayout(self)
        else:
            main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._label = QLabel(self)
        self._label.setObjectName('label')
        self._label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        main_layout.addWidget(self._label)

        self._layout2 = QHBoxLayout(self)
        main_layout.addLayout(self._layout2)
        if direction == 'vertical':
            self._label.setAlignment(Qt.AlignLeft | Qt .AlignVCenter)
        else:
            self._label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    @staticmethod
    def to_title(name):
        """
        Converts camel case strings to title strings
        :param name: str
        :return: str
        """

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).title()

    @decorators.abstractmethod
    def value(self):
        """
        Returns the current value fo the field widget
        :return: variant
        """

        raise NotImplementedError('value function of FieldWidget is not implemented!')

    @decorators.abstractmethod
    def set_items(self, items):
        """
        Sets the items for the field widget
        :param items: list(str)
        """

        raise NotImplementedError('set_items function of FieldWidget is not implemented!')

    def label(self):
        """
        Returns label widget
        :return: QLabel
        """

        return self._label

    def title(self):
        """
        Returns the title to be displayed for the field
        :return: str
        """

        data = self.data()
        title = data.get('title', '') or data.get('name', '')
        if title:
            title = self.to_title(title)

        if self.is_required():
            title += '*'

        return title

    def is_default(self):
        """
        Returns whether the current value is the same as the default value or not
        :return: bool
        """

        return self.value() == self.default()

    def default(self):
        """
        Returns the default value for the field widget
        :return: variant
        """

        return self._default

    def set_default(self, default):
        """
        Sets teh default value for the field widget
        :param default: variant
        """

        self._default = default

    def set_text(self, text):
        """
        Sets the label text for the field widget
        :param text: str
        """

        self._label.setText(text)

    def set_value(self, value):
        """
        Sets the value of the field widget
        :param value: variant
        """

        self._on_emit_value_changed()

    def state(self):
        """
        Returns the current state of the data
        :return: dict
        """

        return {
            'name': self._data['name'],
            'value': self.value()
        }

    def data(self):
        """
        Returns the data for the widget
        :return: dict
        """

        return self._data

    def set_data(self, data):
        """
        Sets the current state of the field widget using a dictionary
        :param data: dict
        """

        state = data
        self.blockSignals(True)

        try:
            items = state.get('items', None)
            if items is not None:
                self.set_items(items)
            value = state.get('value', None)
            default = state.get('default', None)
            if default is not None:
                self.set_default(default)
            elif value is not None:
                self.set_default(value)
            if value is not None and value != self.value():
                try:
                    self.set_value(value)
                except TypeError as e:
                    qt.logger.exception('{} | {}'.format(e, traceback.format_exc()))
            enabled = state.get('enabled', None)
            if enabled is not None:
                self.setEnabled(enabled)
                self._label.setEnabled(enabled)
            hidden = state.get('hidden', None)
            if hidden is not None:
                self.setHidden(hidden)
            required = state.get('required', None)
            if required is not None:
                self.set_required(required)
            error = state.get('error', None)
            if error is not None:
                self.set_error(error)
            tooltip = state.get('toolTip', None)
            if tooltip is not None:
                self.setToolTip(tooltip)
                self.setStatusTip(tooltip)
            style = state.get('style', None)
            if style is not None:
                self.setStyleSheet(style)
            title = self.title() or ''
            self.set_text(title)
            lbl = state.get('label')
            if lbl is not None:
                text = lbl.get('name', None)
                if text is not None:
                    self.set_text(text)
                visible = lbl.get('visible', None)
                if visible is not None:
                    self.label().setVisible(visible)
            actions = state.get('actions', None)
            if actions is not None:
                self._menu_button.setVisible(True)
            menu = state.get('menu', None)
            if menu is not None:
                text = menu.get('name')
                if text is not None:
                    self._menu_button.setText(text)
                visible = menu.get('visible', True)
                self._menu_button.setVisible(visible)
            self._data.update(data)
            self.refresh()
        finally:
            self.blockSignals(False)

    def set_error(self, message):
        """
        Sets the error message to be displayed for the field widget
        :param message: str
        """

        self._error = True if message else False
        self._data['error'] = message
        if self._error:
            self._error_label.setText(message)
            self._error_label.setHidden(False)
            self.setToolTip(message)
        else:
            self._error_label.setText('')
            self._error_label.setHidden(True)
            self.setToolTip(self.data().get('toolTip'))

        self.refresh()

    def widget(self):
        """
        Returns the widget used to set and get the field value
        :return: QWidget
        """

        return self._widget

    def set_widget(self, widget):
        """
        Sets the widget used to set and get the field value
        :param widget: QWidget
        """

        widget_layout = QHBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(0)

        self._widget = widget
        self._widget.setParent(self)
        self._widget.setObjectName('widget')
        self._widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._menu_button = QPushButton('...')
        self._menu_button.setHidden(True)
        self._menu_button.setObjectName('menuButton')
        self._menu_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._menu_button.clicked.connect(self._on_menu_callback)

        widget_layout.addWidget(self._widget)
        widget_layout.addWidget(self._menu_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._error_label = QLabel(self)
        self._error_label.setHidden(True)
        self._error_label.setObjectName('errorLabel')
        self._error_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addLayout(widget_layout)
        layout.addWidget(self._error_label)

        self._layout2.addLayout(layout)

    def is_required(self):
        """
        Returns whether current field is required for the field widget or not
        :return: bool
        """

        return bool(self._required)

    def set_required(self, flag):
        """
        Sets whether the field is required for the field widget or not
        :param flag: bool
        """

        self._required = flag
        self.setProperty('required', flag)
        self.setStyleSheet(self.styleSheet())

    def reset(self):
        """
        Resets the field widget back to its default values
        """

        self.set_state(self._data)

    def refresh(self):
        """
        Refresh the style properties of the field
        """

        direction = self._data.get('layout', self.DefaultLayout)
        self.setProperty('layout', direction)
        self.setProperty('default', self.is_default())
        self.setProperty('error', self._error)
        self.setStyleSheet(self.styleSheet())

    def _action_callback(self, callback):
        """
        Internal function that wraps schema callback to get the return value
        :param callback: fn
        """

        self._action_result = callback()

    def _on_menu_callback(self):
        """
        Internal callback function that is triggered when the menu button is clicked
        """

        callback = self.data().get('menu', {}).get('callback', self._on_how_menu)
        callback()

    def _on_show_menu(self):
        """
        Internal callback that shows field menu using the actions from the data
        """

        menu = QMenu(self)

        actions = self.data().get('actions', [])
        for action in actions:
            name = action.get('name', 'No name found')
            callback = action.get('callback')
            fn = partial(self._action_callback, callback)
            action = menu.addAction(name)
            action.triggered.connect(fn)

        point = QCursor.pos()
        point.setX(point.x() + 3)
        point.setY(point.y() + 3)

        self._action_result = None

        menu.exec_(point)

        if self._action_result is not None:
            self.set_value(self._action_result)

    def _on_emit_value_changed(self, *args):
        """
        Emits the value changed signal
        :param args: list
        """

        self.valueChanged.emit()
        self.refresh()


class BoolFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(BoolFieldWidget, self).__init__(*args, **kwargs)

        widget = QCheckBox(self)
        widget.stateChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)
        inline = self.data().get('inline')
        if inline:
            self.label().setText('')
            self.widget().setText(self.title())

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the checkbox
        :return: str
        """

        return bool(self.widget().isChecked())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the checkbox
        :param value: str
        """

        self.widget().setChecked(value)
        super(BoolFieldWidget, self).set_value(value)


class IntFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(IntFieldWidget, self).__init__(*args, **kwargs)

        validator = QIntValidator(-sys.maxint, sys.maxint, self)

        widget = QLineEdit(self)
        widget.setValidator(validator)
        widget.stateChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        value = self.widget().text()
        if value.strip() == '':
            value = self.default()

        return int(str(value))

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        if value == '':
            value = self.default()
        self.widget().setText(str(int(value)))


class SliderFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(SliderFieldWidget, self).__init__(*args, **kwargs)

        widget = QSlider(self)
        widget.setOrientation(Qt.Horizontal)
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        widget.valueChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the slider
        :return: str
        """

        return self.widget().value()

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the slider
        :param value: str
        """

        self.widget().setValue(value)


class RangeFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(RangeFieldWidget, self).__init__(*args, **kwargs)

        widget = QFrame(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        widget.setLayout(layout)

        validator = QIntValidator(-sys.maxint, sys.maxint, self)

        self._min_widget = QLineEdit(self)
        self._min_widget.setValidator(validator)
        self._min_widget.textChanged.connect(self._on_emit_value_changed)
        widget.layout().addWidget(self._min_widget)

        self._max_widget = QLineEdit(self)
        self._max_widget.setValidator(validator)
        self._max_widget.textChanged.connect(self._on_emit_value_changed)
        widget.layout().addWidget(self._max_widget)

        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the current range
        :return: list(int)
        """

        min_value = int(float(self._min_widget.text() or '0'))
        max_value = int(float(self._max_widget.text() or '0'))

        return min_value, max_value

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the current range
        :param value: list(int)
        """

        min_value, max_value = int(value[0], int(value[1]))
        self._min_widget.setText(str(min_value))
        self._max_widget.setText(str(max_value))

        super(RangeFieldWidget, self).set_value(value)


class StringFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(StringFieldWidget, self).__init__(*args, **kwargs)

        widget = label.QLineEdit(self)
        widget.textChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        return str(self.widget().text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        self.widget().setText(value)
        super(StringFieldWidget, self).set_value(value)


class PasswordFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(PasswordFieldWidget, self).__init__(*args, **kwargs)

        widget = label.QLineEdit(self)
        widget.setEchoMode(QLineEdit.EchoMode.Password)
        widget.textChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the widget
        :return: str
        """

        return str(self.widget().text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the widget
        :param value: str
        """

        self.widget().setText(value)
        super(PasswordFieldWidget, self).set_value(value)


class TextFieldWidget(FieldWidget, object):

    DefaultLayout = 'vertical'

    def __init__(self, *args, **kwargs):
        super(TextFieldWidget, self).__init__(*args, **kwargs)

        widget = label.QTextEdit(self)
        widget.textChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the text edit
        :return: str
        """

        return str(self.widget().toPlainText())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the text edit
        :param value: str
        """

        self.widget().setText(value)
        super(TextFieldWidget, self).set_value(value)


class PathFieldWidget(StringFieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(PathFieldWidget, self).__init__(*args, **kwargs)

    def set_data(self, data):
        """
        Overrides StringFieldWidget set_data function
        Adds a browse button to folder button
        :param data: dict
        """

        if 'menu' not in data:
            data['menu'] = {
                'callback': self._on_browse
            }
        super(PathFieldWidget, self).set_data(data)

    def _on_browse(self):
        """
        Opens file dialog
        """

        path = self.value()
        path = QFileDialog.getExistingDirectory(None, 'Browse Folder', path)
        if path:
            self.set_value(path)

        widget = QCheckBox(self)
        widget.stateChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)
        inline = self.data().get('inline')
        if inline:
            self.label().setText('')
            self.widget().setText(self.title())


class LabelFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(LabelFieldWidget, self).__init__(*args, **kwargs)

        widget = label.RightElidedLabel(self)
        widget.setAlignment(Qt.AlignVCenter)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the label
        :return: str
        """

        return str(self.widget().text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the label
        :param value: str
        """

        self.widget().setText(value)
        super(LabelFieldWidget, self).set_value(value)


class EnumFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(EnumFieldWidget, self).__init__(*args, **kwargs)

        widget = QComboBox(self)
        widget.currentIndexChanged.connect(self._on_emit_value_changed)
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the combo box
        :return: str
        """

        return str(self.widget().currentText())

    def set_value(self, item):
        """
        Overrides FileWidget set_value function
        Sets the value of the combo box
        :param item: str
        """

        self.set_current_text(item)

    def set_items(self, items):
        """
        Overrides FieldWidget set_items function
        Sets the current items of the combo box
        :param items: list(str)
        """

        self.widget().clear()
        self.widget().addItems(items)

    def set_state(self, state):
        """
        Sets the current state with support for editable
        :param state: dict
        """

        super(EnumFieldWidget, self).set_state(state)
        editable = state.get('editable')
        if editable is not None:
            self.widget().setEditable(editable)

    def set_current_text(self, text):
        """
        Sets current text
        :param text: str
        """

        index = self.widget().findText(text, Qt.MatchExactly)
        if index != -1:
            self.widget().setCurrentIndex(index)
        else:
            qt.logger.warning('Cannot set the value for field {}'.format(self.name()))


class SeparatorFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(SeparatorFieldWidget, self).__init__(*args, **kwargs)

        widget = QLabel(self)
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.label().hide()
        self.set_widget(widget)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the separator
        :return: str
        """

        return str(self.widget().text())

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the separator
        :param value: str
        """

        self.widget().setText(value)


class ColorFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(ColorFieldWidget, self).__init__(*args, **kwargs)

        widget = color.ColorPicker()
        widget.setObjectName('widget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        widget.colorChanged.connect(self._on_color_changed)
        self.set_widget(widget)

    def set_data(self, data):
        """
        Overrides FieldWidget data function
        :param data: dict
        """

        colors = data.get('colors')
        if colors:
            self.widget().set_colors(colors)

        super(ColorFieldWidget, self).set_data(data)

    def value(self):
        """
        Implements FieldWidget value function
        Returns the value of the color picker
        :return: Color
        """

        return self.widget().current_color()

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the value of the color picker
        :param value: str
        """

        self.widget().set_current_color(value)

    def _on_color_changed(self, new_color):
        """
        Internal callback function triggered when the color changes from the color browser
        :param new_color: QColor
        """

        self.set_value(new_color)
        self._on_emit_value_changed()


class ImageFieldWidget(FieldWidget, object):
    def __init__(self, *args, **kwargs):
        super(ImageFieldWidget, self).__init__(*args, **kwargs)

        self._value = ''
        self._pixmap = None

        widget = QLabel(self)
        widget.setObjectName('widget')
        self.setStyleSheet('min-height: 32px;')
        widget.setScaledContents(False)
        widget.setAlignment(Qt.AlignHCenter)
        self.set_widget(widget)
        self.layout().addStretch()

    def resizeEvent(self, event):
        """
        Overrides FieldWidget resizeEvent function
        Called when teh field widget is resized
        :param event: QResizeEvent
        """

        self.update()

    def value(self):
        """
        Implements FieldWidget value function
        Returns the path of the image in disk
        :return: str
        """

        return self._value

    def set_value(self, value):
        """
        Overrides FileWidget set_value function
        Sets the path of the image in disk
        :param value: str
        """

        self._value = value
        self._pixmap = QPixmap(value)
        self.update()

    def update(self):
        """
        Updates the image depending on the size
        """

        if not self._pixmap:
            return

        width = self.widget().height()
        if self.widget().width() > self.widget().height():
            pixmap = self._pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        else:
            pixmap = self._pixmap.scaledToHeight(width, Qt.SmoothTransformation)
        self.widget().setPixmap(pixmap)
        self.widget().setAlignment(Qt.AlignLeft)


FIELD_WIDGET_REGISTRY = {
    "int": IntFieldWidget,
    "bool": BoolFieldWidget,
    "enum": EnumFieldWidget,
    "text": TextFieldWidget,
    "path": PathFieldWidget,
    "image": ImageFieldWidget,
    "label": LabelFieldWidget,
    "range": RangeFieldWidget,
    "color": ColorFieldWidget,
    "string": StringFieldWidget,
    "password": PasswordFieldWidget,
    "slider": SliderFieldWidget,
    "separator": SeparatorFieldWidget
}
