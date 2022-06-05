import math

import cv2
import numpy as np


def stretch_width(edges, img_shape):
    [up, down, left, right] = edges
    (h, w) = img_shape[:2]

    # find intersection of 'up' with x=0 and x=w
    a = get_angle(up[0], up[1])
    x0, y0 = up[0]
    top_left = [0, int(y0-a*x0)]
    top_right = [w, int(a*w + y0 - a*x0)]

    # find intersection of 'down' with x=0 and x=w
    a = get_angle(down[0], down[1])
    x0, y0 = down[0]
    bottom_left = [0, int(y0-a*x0)]
    bottom_right = [w, int(a * w + y0 - a * x0)]

    # return new [up, down, left, right]
    return [[top_left, top_right], [bottom_left, bottom_right], [top_left, bottom_left], [top_right, bottom_right]]


def stretch_up(edges, img_shape):
    [up, down, left, right] = edges
    (h, w) = img_shape[:2]

    # find intersection of 'left' with y=0
    a = get_angle(left[0], left[1])
    x0, y0 = left[0]
    if a == "vertical":
        top_left = [x0, 0]
    else:
        top_left = [int(x0-y0/a), 0]

    # find intersection of 'right' with y=0
    a = get_angle(right[0], right[1])
    x0, y0 = right[0]
    if a == "vertical":
        top_right = [x0, 0]
    else:
        top_right = [int(x0 - y0 / a), 0]

    bottom_left = max(left, key=lambda p: p[1])
    bottom_right = max(right, key=lambda p: p[1])

    # return new [up, down, left, right]
    return [[top_left, top_right], [bottom_left, bottom_right], [top_left, bottom_left], [top_right, bottom_right]]


def create_mask_inside_edges(edges, img_shape):
    [up, down, left, right] = edges
    top_left = get_common_point(up, left)
    bottom_left = get_common_point(left, down)
    bottom_right = get_common_point(down, right)
    top_right = get_common_point(right, up)
    mask = get_black_image(img_shape)
    mask = cv2.fillConvexPoly(mask, np.array([top_left, bottom_left, bottom_right, top_right]), (255,255,255))
    return mask


def get_common_point(e1, e2):
    return min(e1, key=lambda p_e1: min(dis(p_e1, e2[0]), dis(p_e1, e2[1])))


def dis(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def rotate_edge(edge, M):
    [p1, p2] = edge
    p1 = np.array(p1)
    p1 = np.append(p1, 1)
    p1 = np.dot(M, p1)

    p2 = np.array(p2)
    p2 = np.append(p2, 1)
    p2 = np.dot(M, p2)

    return [p1, p2]


def find_edges(box2d):
    p = np.int0(cv2.boxPoints(box2d))
    p = sorted(p, key=lambda p: p[0])
    if p[2][0] == p[3][0] or p[2][1] == p[3][1]:  # if there is no N-shape in points order - replace
        p[2], p[3] = p[3], p[2]
    e1, e2, e3, e4 = [p[0], p[1]], [p[0], p[2]], [p[2], p[3]], [p[1], p[3]]  # e1 is parallel to e3, e2 parallel to e4

    e1_angle = get_angle(e1[0], e1[1])
    if e1_angle == "vertical" or abs(e1_angle) > 1:
        left = e1
        right = e3
        up = min([e2, e4], key=lambda e: get_middle_of_edge(e)[1])  # minimum of average of height
        down = max([e2, e4], key=lambda e: get_middle_of_edge(e)[1])
    else:
        # e1 is either up or down
        up = min([e1, e3], key=lambda e: get_middle_of_edge(e)[1])
        down = max([e1, e3], key=lambda e: get_middle_of_edge(e)[1])
        left = e2
        right = e4
    return [up, down, left, right]


def get_middle_of_edge(edge):
    p1, p2 = edge[0], edge[1]
    return [(p1[0] + p2[0])/2, (p1[1] + p2[1])/2]


def get_angle(p1, p2):
    delta_y = p2[1] - p1[1]
    delta_x = p2[0] - p1[0]
    if delta_x == 0:
        return "vertical"
    return delta_y / delta_x


def draw_rectangles_from_ocr_data(a_img, d):
    img = a_img.copy()
    n_boxes = len(d['level'])
    for i in range(n_boxes):
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return img


def draw_points(a_img, points):
    img = a_img.copy()
    for point in points:
        img = cv2.circle(img, point, radius=3, color=(255, 255, 255), thickness=-1)
    return img


def get_black_image(img_shape):
    (h, w) = img_shape[:2]
    return np.zeros((h, w, 1), dtype = "uint8")


def print_img(win_name, img):
    cv2.imshow(win_name, img)
    cv2.waitKey(0)