import sys
import os
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import graphics as gr
import math

pytesseract.pytesseract.tesseract_cmd = r'D:\tesseract\tesseract.exe'

# estimated constants
MIN_RECT_WIDTH = 0.0121
MAX_RECT_WIDTH = 0.17
MIN_RETT_HEIGHT = 0.008
MAX_RECT_HEIGHT = 0.03
MAX_CLUSTER_DIS = 0.06
MAX_MARGIN_DIS = 0.17  # originally, the max width was 2/3 -> margin is 1/6, but I took some spair
MAX_ROTATION_ANGLE = 10

DEBUG_MODE = False

# TODO:
#  add option to include areas like page number in mask, but not to include them in the aligning and centering
#  add option not to clear the edges, only rotate and shift


def main():
    input_img_path = ""
    output_img_path = "result_aligned.jpg"
    output_steps_path = r'image_steps'

    # defining pathes
    arg_num = len(sys.argv)
    if arg_num >= 3:  # script name, input image path, output image path
        input_img_path = sys.argv[1]
        output_img_path = sys.argv[2]
    if arg_num == 4:
        output_steps_path = sys.argv[3]

    if not os.path.isfile(input_img_path):
        print("image not found, missing path is: " + input_img_path)
        return

    # read image
    img = cv2.imread(input_img_path, cv2.IMREAD_GRAYSCALE)
    if DEBUG_MODE:
        if not os.path.isdir(output_steps_path):
            os.mkdir(output_steps_path)
        cv2.imwrite(output_steps_path + r'\1_image.jpg', img)

    # get ocr data using pytesseract-ocr
    ocr_data = pytesseract.image_to_data(img, output_type=Output.DICT)
    #if DEBUG_MODE:
    #    cv2.imwrite(output_steps_path + r'\1_5_all_rectangles.jpg', gr.draw_rectangles_from_ocr_data(img, ocr_data))

    # filter bad rectangles - by size, 'level' and clusters
    (h, w) = img.shape[:2]
    ocr_data = filter_by_size_and_level(ocr_data, h, w)
    rects_points = get_points_of_ocr_data(ocr_data)
    # filter by clusters
    rects_points = filter_by_clusters(rects_points, img_scale=(w+h)/2)
    if DEBUG_MODE:
        cv2.imwrite(output_steps_path + r'\2_rectangles.jpg', gr.draw_rectangles_from_ocr_data(img, ocr_data))

    # create black image with white points in the edges of the rectangles - for debugging
    if DEBUG_MODE:
        points_img = gr.draw_points(gr.get_white_image(img.shape), rects_points)
        cv2.imwrite(output_steps_path + r'\3_points_img.jpg', points_img)

    # make sure there are rect_points
    if not rects_points:
        cv2.imwrite(output_steps_path + r'\6_img_result.jpg', img)
        cv2.imwrite(output_img_path, img)
        return

    # find min rectangle around the rects_points
    box2d = cv2.minAreaRect(np.array(rects_points))  # box2d = (center(x, y), (w, h), angle)
    points = np.int0(cv2.boxPoints(box2d))

    # draw polylines of box2d - for debugging
    if DEBUG_MODE:
        img_with_box2d = cv2.polylines(img.copy(), [points], isClosed=True, color=(0,0,0), thickness=3)
        cv2.imwrite(output_steps_path + r'\4_img_with_box2d.jpg', img_with_box2d)

    # aligning, if all the conditions are met
    box_angle = box2d[2] if box2d[2] < 45 else box2d[2] - 90
    if not -MAX_ROTATION_ANGLE < box_angle < MAX_ROTATION_ANGLE:  # the recognition failed for some reason and the angle is not valid - do nothing
        if DEBUG_MODE:
            cv2.imwrite(output_steps_path + r'\6_img_result.jpg', img)
        cv2.imwrite(output_img_path, img)
    else:
        img_mask, x_shift, y_shift = proccess_box2d(box2d, img.shape)
        if DEBUG_MODE:
            cv2.imwrite(output_steps_path + r'\5_img_mask.jpg', img_mask)

        # find the rotation+shift matrix
        M = cv2.getRotationMatrix2D(center=box2d[0], angle=box_angle, scale=1)
        M[0][2] += x_shift
        M[1][2] += y_shift

        # rotate+shift
        rotated_img = cv2.warpAffine(img, M, dsize=(w, h), borderValue=(255,255,255))
        rotated_mask = cv2.warpAffine(img_mask, M, dsize=(w, h), borderValue=(255,255,255))
        result = cv2.bitwise_or(rotated_img, rotated_mask)

        if DEBUG_MODE:
            cv2.imwrite(output_steps_path + r'\6_img_result.jpg', result)
        cv2.imwrite(output_img_path, result)


def proccess_box2d(box2d, img_shape):
    """
    1. define x_shift, y_shift so that the box will be centered
    2. define up, down, left, right edges ([p1, p2] that defines the edge)
    2. check for each direction the distant to the end of the image (average distance, that will remain after rotation)
    3. stretch borders in mask for those that aren't close enough, and zero the relevant shifts
    4. return :)
    :param box2d: the box to process
    :param img_shape: shape of the image, (h, w)
    :return: image mask, x_shift, y_shift
    """
    # find x_shift, y_shift
    (center_x, center_y) = box2d[0]
    (h, w) = img_shape[:2]
    x_shift = w/2 - center_x
    y_shift = h/2 - center_y

    # find up, down, left, right edges ([p1, p2] that defines the edge)
    edges = gr.find_edges(box2d)
    [up, down, left, right] = edges

    # check the distance to the end of the image, to decide if there was a mistake in recognition
    box_angle = box2d[2] if box2d[2] < 45 else -(90 - box2d[2])
    M = cv2.getRotationMatrix2D(center=box2d[0], angle=box_angle, scale=1)
    [r_up, r_down, r_left, r_right] = [gr.rotate_edge(edge, M) for edge in edges]
    if (r_left[0][0] + w-r_right[0][0]) > 2*MAX_MARGIN_DIS * w:  # if the width is too thin
        x_shift = 0
        edges = gr.stretch_width(edges, img_shape)
    if r_up[1][1] > MAX_MARGIN_DIS * w:  # if the height is too low. Assumption - the image starts relatively high
        y_shift = 0
        edges = gr.stretch_up(edges, img_shape)
    elif h-r_down[1][1] > MAX_MARGIN_DIS * w:  # if there is a text in the upper part - it should stay there
        y_shift = 0

    # create mask using the edges
    img_mask = gr.create_mask_inside_edges(edges, img_shape)

    return img_mask, x_shift, y_shift


def filter_by_clusters(rects_points, img_scale):
    if not rects_points:
        return rects_points

    clusters = []
    for i in range(int(len(rects_points)/4)):
        rect = rects_points[4*i: 4*(i+1)]  # [p1, p2, p3, p4]

        # find all the clusters the rectangle is close to
        close_clusters = []
        for i_cluster in range(len(clusters)):
            if cluster_dis(rect, clusters[i_cluster]) < MAX_CLUSTER_DIS*img_scale:
                close_clusters.append(i_cluster)

        # create new cluster/ add the rectangle to the relevant cluster (and merge clusters)
        if not close_clusters:
            clusters.append(rect)
        else:
            # adding the rect to the first close cluster
            clusters[close_clusters[0]].extend(rect)

            # merge clusters into the first close_cluster, if needed
            for i_cluster in reversed(close_clusters[1:]):
                clusters[close_clusters[0]].extend(clusters.pop(i_cluster))

    # include only the clusters that are "big enough" - at least 1/5 of the biggest cluster
    rects_points = []
    max_cluster = len(max(clusters, key=lambda c: len(c)))
    for c in clusters:
        if len(c) > 0.2*max_cluster:
            rects_points.extend(c)

    return rects_points


def cluster_dis(rect, cluster):
    return min([dis(p_rect, p_cluster) for p_cluster in cluster for p_rect in rect])


def dis(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)


def get_points_of_ocr_data(d):
    points = []
    for i in range(len(d['level'])):
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        points.extend([[x, y], [x, y+h], [x+w, y+h], [x+w, y]])
    return points


def filter_by_size_and_level(d, img_h, img_w):
    # TODO: check if I should use 'conf' instead of 'level'. level relates to the amount of data I have, conf relates to the confidence in recognition
    n_boxes = len(d['level'])
    for i in reversed(range(n_boxes)):
        level, w, h = d['level'][i], d['width'][i], d['height'][i]
        if level < 5 or w < MIN_RECT_WIDTH*img_w or w > MAX_RECT_WIDTH*img_w or h < MIN_RETT_HEIGHT*img_h or h > MAX_RECT_HEIGHT*img_h:
            # delete this rectangle
            for element in d:
                d[element].pop(i)
    return d


if __name__ == "__main__":
    main()



