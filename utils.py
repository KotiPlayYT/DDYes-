# utils.py
import math


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def lerp(a, b, t):
    return a + (b - a) * t