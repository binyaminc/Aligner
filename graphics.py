import cv2
import numpy as np


def draw_rectangles(a_img, d):
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