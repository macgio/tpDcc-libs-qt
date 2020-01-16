#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality related with SVG operations
"""

from __future__ import print_function, division, absolute_import

import math
import os
import re
from xml.dom import minidom

from Qt.QtCore import *
from Qt.QtGui import *


_COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
_COMMAND_RE = re.compile('([MmZzLlHhVvCcSsQqTtAa])')
_FLOAT_RE = re.compile('[-+]?[0-9]*\\.?[0-9]+(?:[eE][-+]?[0-9]+)?')


def generate_svg(svg_file):

    draw_set = list()
    bounding_rect = QRectF()

    for style, path, pathType, id in get_path_order_from_svg_file(svg_file):

        # We do not load the init rect item which indicates document settings
        if style.get('display') == 'none':
            continue
        if pathType == 'path':
            svgPath = create_svg_path(path)
        elif pathType in ('circle', 'ellipse'):
            svgPath = create_ellipse_path(path)
        elif pathType == 'rect':
            svgPath = create_rect_path(path)
        elif pathType == 'polygon':
            svgPath = create_polygon_path(path)
        else:
            continue
        bounding_rect = bounding_rect.united(svgPath.boundingRect())
        draw_set.append([style, svgPath])

    for bundle in draw_set:
        path = bundle.pop()
        offset = path.boundingRect().topLeft() - bounding_rect.topLeft()
        path.translate(path.boundingRect().topLeft() * -1)
        path.translate(offset)
        bundle.append(path)

    return (bounding_rect, draw_set)


def get_style_tag(doc):

    root = doc.documentElement
    for node in root.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == 'style':
            result = dict()
            for data in node.firstChild.data.strip().split():
                m = re.match('^\\.(.+)\\{(.+)\\}$', data)
                if m:
                    result[m.group(1)] = dict([s.split(':') for s in m.group(2).split(':') if s])
            return ('styleElement', result)
    return ('styleAttribute', {})


def get_all_svg_tags(doc):
    def check_tag_name(root, listData=[]):
        if root.childNodes:
            for node in root.childNodes:
                if node.nodeType == node.ELEMENT_NODE:
                    if node.tagName in ('path', 'circle', 'ellipse', 'rect', 'polygon'):
                        listData.append(node)
                    check_tag_name(node, listData)
    root = doc.documentElement
    l = list()
    check_tag_name(root, l)
    return l


def decode_svg_path_string_replace(pathString):
    d = _tokenize_path_replace(pathString)
    path_order = list()
    pop_data = d.pop(0)
    while d:
        if pop_data and pop_data.isalpha():
            numeric_buffer = list()
            try:
                num = d.pop(0)
                while not num.isalpha():
                    numeric_buffer.append(float(num))
                    num = d.pop(0)
                path_order.append((pop_data, numeric_buffer))
                pop_data = num
            except IndexError:
                path_order.append((pop_data, numeric_buffer))
    return path_order


def decode_svg_path_string(pathString):
    token = _tokenize_path(pathString)
    path_order = list()
    d = token.next()
    while token:
        try:
            if d.isalpha():
                numeric_buffer = list()
                num = token.next()
                while not num.isalpha():
                    numeric_buffer.append(float(num))
                    num = token.next()
                path_order.append((d, numeric_buffer))
                d = num
        except:
            path_order.append((d, numeric_buffer))
            break
    return path_order


def get_path_order_from_svg_file(svgFile):

    if not os.path.isfile(svgFile):
        print('ERROR: Svg file {} doest not exists!'.format(svgFile))
        return

    doc = minidom.parse(svgFile)
    style_type, styleRef = get_style_tag(doc)
    all_svg_tags = get_all_svg_tags(doc)
    result = list()

    for tag in all_svg_tags:
        id = tag.getAttribute('id').replace('_x5F_', '_')       # Get SVG layer name (id)
        if not id:
            id = None
        style_dict = dict()
        if style_type == 'styleElement' and tag.hasAttribute('class'):
            style = tag.getAttribute('class')
            if style in styleRef:
                style_dict = styleRef[style]
        elif style_type == 'styleAttribute':
            if tag.hasAttribute('style'):
                style = tag.getAttribute('style')
                style_dict = dict([s.split(':') for s in style.split(';') if s])
            else:
                for attr in ['fill', 'stroke', 'stroke-width', 'display']:
                    if tag.hasAttribute(attr):
                        style_dict[attr] = tag.getAttribute(attr)

        if tag.tagName == 'path':
            path = tag.getAttribute('d')
            path_order = decode_svg_path_string_replace(path)
        elif tag.tagName == 'circle':
            path_order = dict()
            path_order['cx'] = float(tag.getAttribute('cx'))
            path_order['cy'] = float(tag.getAttribute('cy'))
            path_order['rx'] = float(tag.getAttribute('r'))
            path_order['ry'] = float(tag.getAttribute('r'))
        elif tag.tagName == 'ellipse':
            path_order = {}
            path_order['cx'] = float(tag.getAttribute('cx'))
            path_order['cy'] = float(tag.getAttribute('cy'))
            path_order['rx'] = float(tag.getAttribute('rx'))
            path_order['ry'] = float(tag.getAttribute('ry'))
            path_order['transform'] = tag.getAttribute('transform') or ''
        elif tag.tagName == 'rect':
            path_order = {}
            x = tag.getAttribute('x')
            path_order['x'] = x and float(x) or 0.0
            y = tag.getAttribute('y')
            path_order['y'] = y and float(y) or 0.0
            path_order['w'] = float(tag.getAttribute('width'))
            path_order['h'] = float(tag.getAttribute('height'))
            rx = tag.getAttribute('rx')
            path_order['rx'] = rx and float(rx) or 0.0
            ry = tag.getAttribute('ry')
            path_order['ry'] = ry and float(ry) or 0.0
            path_order['transform'] = tag.getAttribute('transform') or ''
        elif tag.tagName == 'polygon':
            path_order = {}
            points = tag.getAttribute('points').strip()
            pnt = []
            for seg in points.split(' '):
                x, y = seg.split(',')
                pnt.append(QPointF(float(x), float(y)))
            path_order['points'] = pnt
        result.append((style_dict, path_order, tag.tagName, id))
    doc.unlink()
    return result


def create_svg_path(orders, verbose = False):
    path = QPainterPath()
    for k, order in enumerate(orders):
        if order[0] == 'M' or order[0] == 'm':
            if verbose:
                print(k, 'MOVE TO', order[1])
            move_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'C' or order[0] == 'c':
            if verbose:
                print(k, 'CUBIC TO', order[1])
            cubic_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'S' or order[0] == 's':
            if verbose:
                print(k, 'SMOOTH CUBIC TO', order[1])
            smooth_cubic_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'Q' or order[0] == 'q':
            if verbose:
                print(k, 'QUAD TO', order[1])
            quad_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'T' or order[0] == 't':
            if verbose:
                print(k, 'SMOOTH QUAD TO', order[1])
            smooth_quad_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'H' or order[0] == 'h':
            if verbose:
                print(k, 'HORIZONTAL LINE TO', order[1])
            horizontal_line_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'V' or order[0] == 'v':
            if verbose:
                print(k, 'VERTICAL LINE TO', order[1])
            vertical_line_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'L' or order[0] == 'l':
            if verbose:
                print(k, 'LINE TO', order[1])
            line_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'A' or order[0] == 'a':
            if verbose:
                print(k, 'ARC TO', order[1])
            arc_to(path, *order)
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif order[0] == 'z' or order[0] == 'Z':
            if verbose:
                print(k, 'close sub path')
            path.closeSubpath()
            if verbose:
                print(path.elementAt(path.elementCount() - 1).type)
        elif verbose:
            print(k, order)

    if verbose:
        print('------------end-------------')
    return path


def create_ellipse_path(data):
    path = QPainterPath()
    path.addEllipse(QPointF(data.get('cx'), data.get('cy')), data.get('rx'), data.get('ry'))
    if 'transform' in data:
        m = re.match('^matrix\\((.+)\\)$', data.get('transform'))
        if m:
            args = map(lambda x: float(x), m.group(1).split())
            if len(args) == 6:
                transform = QTransform(*args)
                path *= transform
    return path


def create_rect_path(data):
    path = QPainterPath()
    if data.get('rx') > 0 or data.get('ry'):
        path.addRoundedRect(data.get('x'), data.get('y'), data.get('w'), data.get('h'), data.get('rx'), data.get('ry'))
    else:
        path.addRect(data.get('x'), data.get('y'), data.get('w'), data.get('h'))
    if 'transform' in data:
        m = re.match('^matrix\\((.+)\\)$', data.get('transform'))
        if m:
            args = map(lambda x: float(x), m.group(1).split())
            if len(args) == 6:
                transform = QTransform(*args)
                path *= transform
    return path


def create_polygon_path(data):
    path = QPainterPath()
    polygon = QPolygonF()
    for pt in data.get('points'):
        polygon.append(pt)

    path.addPolygon(polygon)
    return path


def generate_path_to_svg(path):
    d = ''
    for i in range(path.elementCount()):
        element = path.elementAt(i)
        if element.type == QPainterPath.ElementType.MoveToElement:
            d += 'M%.3f,%.3f' % (element.x, element.y)
        elif element.type == QPainterPath.ElementType.CurveToElement:
            d += 'C%.3f,%.3f,' % (element.x, element.y)
        elif element.type == QPainterPath.ElementType.CurveToDataElement:
            d += '%.3f,%.3f' % (element.x, element.y)
            if path.elementAt(i + 1).type == QPainterPath.ElementType.CurveToDataElement:
                d += ','
        elif element.type == QPainterPath.ElementType.LineToElement:
            d += 'L%.3f,%.3f' % (element.x, element.y)
        else:
            print(element.type)

    d += 'Z'
    return d


def calculate_start_angle(x1, y1, rx, ry, coordAngle, largeArcFlag, sweep_flag, x2, y2):

    def dotproduct(v1, v2):
        return sum((a * b for a, b in zip(v1, v2)))

    def length(v):
        return math.sqrt(dotproduct(v, v))

    def angle(v1, v2):
        return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))

    rotated_x1 = math.cos(math.radians(coordAngle)) * ((x1 - x2) / 2) + math.sin(math.radians(coordAngle)) * ((y1 - y2) / 2)
    rotated_y1 = -math.sin(math.radians(coordAngle)) * ((x1 - x2) / 2) + math.cos(math.radians(coordAngle)) * ((y1 - y2) / 2)
    delta = rotated_x1 ** 2 / rx ** 2 + rotated_y1 ** 2 / ry ** 2
    if delta > 1:
        rx *= math.sqrt(delta)
        ry *= math.sqrt(delta)
    var = math.sqrt((rx ** 2 * ry ** 2 - rx ** 2 * rotated_y1 ** 2 - ry ** 2 * rotated_x1 ** 2) / (rx ** 2 * rotated_y1 ** 2 + ry ** 2 * rotated_x1 ** 2))
    if largeArcFlag == sweep_flag:
        var *= -1
    ccx = var * (rx * rotated_y1 / ry)
    ccy = var * -(ry * rotated_x1 / rx)
    cx = math.cos(math.radians(coordAngle)) * ccx - math.sin(math.radians(coordAngle)) * ccy + (x1 + x2) / 2
    cy = math.sin(math.radians(coordAngle)) * ccx + math.cos(math.radians(coordAngle)) * ccy + (y1 + y2) / 2
    start_angle = math.degrees(angle([1, 0], [(rotated_x1 - ccx) / rx, (rotated_y1 - ccy) / ry]))
    start_angle_sign = 1 * (rotated_y1 - ccy) / ry - 0 * (rotated_x1 - ccx) / rx
    if start_angle_sign == 0:
        start_angle_sign = 1.0
    start_angle_sign /= abs(start_angle_sign)
    start_angle *= start_angle_sign
    try:
        sweep_angle = math.degrees(angle([(rotated_x1 - ccx) / rx, (rotated_y1 - ccy) / ry], [(-rotated_x1 - ccx) / rx, (-rotated_y1 - ccy) / ry]))
    except ValueError:
        sweep_angle = 180.0

    sweep_angle_sign = (rotated_x1 - ccx) / rx * (-rotated_y1 - ccy) / ry - (rotated_y1 - ccy) / ry * (-rotated_x1 - ccx) / rx
    if sweep_angle_sign == 0:
        sweep_angle_sign = 1.0
    sweep_angle_sign /= abs(sweep_angle_sign)
    sweep_angle *= sweep_angle_sign
    if sweep_flag == 0 and sweep_angle > 0:
        sweep_angle -= 360
    elif sweep_flag == 1 and sweep_angle < 0:
        sweep_angle += 360
    rect = QRectF(0, 0, rx * 2, ry * 2)
    rect.moveCenter(QPointF(cx, cy))
    return (start_angle, sweep_angle, rect)


def move_to(path, cmd, data):
    target = QPointF(*data)
    if cmd.islower():
        currentPos = path.currentPosition()
        target += currentPos
    path.moveTo(target)


def cubic_to(path, cmd, data):
    new1st_pos = QPointF(data[0], data[1])
    new2st_pos = QPointF(data[2], data[3])
    new_end_pos = QPointF(data[4], data[5])
    if cmd.islower():
        current_pos = path.currentPosition()
        new1st_pos += current_pos
        new2st_pos += current_pos
        new_end_pos += current_pos
    path.cubicTo(new1st_pos, new2st_pos, new_end_pos)


def smooth_cubic_to(path, cmd, data):
    elem_count = path.elementCount()
    prev_end_x, prevEndY = path.elementAt(elem_count - 1).x, path.elementAt(elem_count - 1).y
    prev2nd_x, prev2ndY = path.elementAt(elem_count - 2).x, path.elementAt(elem_count - 2).y
    new1st_pos = QPointF(2 * prev_end_x - prev2nd_x, 2 * prevEndY - prev2ndY)
    new2st_pos = QPointF(data[0], data[1])
    new_end_pos = QPointF(data[2], data[3])
    if cmd.islower():
        current_pos = path.currentPosition()
        new2st_pos += current_pos
        new_end_pos += current_pos
    path.cubicTo(new1st_pos, new2st_pos, new_end_pos)


def quad_to(path, cmd, data):
    new1st_pos = QPointF(data[0], data[1])
    new_end_pos = QPointF(data[2], data[3])
    path.quadTo(new1st_pos, new_end_pos)
    if cmd.islower():
        current_pos = path.currentPosition()
        new1st_pos += current_pos
        new_end_pos += current_pos
    path.quadTo(new1st_pos, new_end_pos)


def smooth_quad_to(path, cmd, data):
    elem_count = path.elementCount()
    prev_end_x, prevEndY = path.elementAt(elem_count - 1).x, path.elementAt(elem_count - 1).y
    prev1st_x, prev1stY = path.elementAt(elem_count - 2).x, path.elementAt(elem_count - 2).y
    new1st_pos = QPointF(2 * prev_end_x - prev1st_x, 2 * prevEndY - prev1stY)
    new_end_pos = QPointF(data[0], data[1])
    if cmd.islower():
        current_pos = path.currentPosition()
        new_end_pos += current_pos
    path.quadTo(new1st_pos, new_end_pos)


def horizontal_line_to(path, cmd, data):
    current_pos = path.currentPosition()
    if cmd.islower():
        target = current_pos + QPointF(data[0], 0)
    else:
        target = QPointF(data[0], current_pos.y())
    path.lineTo(target)


def vertical_line_to(path, cmd, data):
    current_pos = path.currentPosition()
    if cmd.islower():
        target = current_pos + QPointF(0, data[0])
    else:
        target = QPointF(current_pos.x(), data[0])
    path.lineTo(target)


def line_to(path, cmd, data):
    target = QPointF(*data)
    if cmd.islower():
        current_pos = path.currentPosition()
        target += current_pos
    path.lineTo(target)


def arc_to(path, cmd, data):
    current_pos = path.currentPosition()
    x1, y1 = current_pos.x(), current_pos.y()
    rx, ry, angle, fa, fs, x2, y2 = data
    if cmd.islower():
        x2 += x1
        y2 += y1
    start_angle, sweep_angle, rect = calculate_start_angle(x1, y1, rx, ry, angle, fa, fs, x2, y2)
    path.arcTo(rect, -start_angle, -sweep_angle)


def _tokenize_path(pathDef):
    for x in _COMMAND_RE.split(pathDef):
        if x in _COMMANDS:
            yield x
        for token in _FLOAT_RE.findall(x):
            yield token


def _tokenize_path_replace(path_def):
    path_def = path_def.replace('e-', 'NEGEXP').replace('E-', 'NEGEXP')
    path_def = path_def.replace(',', ' ').replace('-', ' -')
    path_def = path_def.replace('NEGEXP', 'e-')
    for c in _COMMANDS:
        path_def = path_def.replace(c, ' %s ' % c)
    return path_def.split()
