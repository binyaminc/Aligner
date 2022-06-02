import sys
import os
import cv2
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

def main():
    input_img_path = r'page221_clusters.jpg'
    output_img_path = r'orig_page_aligned.jpg'
    output_steps_path = r'image_steps'

    # reading image
    arg_num = len(sys.argv)
    if arg_num >= 3:  # script name, input image path, output image path
        input_img_path = sys.argv[1]
        output_img_path = sys.argv[2]
    if arg_num == 4:
        output_steps_path = sys.argv[3]

    if not os.path.isfile(input_img_path):
        print("image not found...")
        return

    # reading image
    img = cv2.imread(input_img_path, cv2.IMREAD_GRAYSCALE)

    # get ocr data using pytesseract-ocr
    ocr_data = pytesseract.image_to_data(img, output_type=Output.DICT)

    # filter bad rectangles - by size, 'level' and clusters
    (h, w) = img.shape[:2]
    ocr_data = filter_by_size_and_level(ocr_data, h, w)
    rects_points = get_points_of_ocr_data(ocr_data)
    # filter by clusters
    rects_points = filter_by_clusters(rects_points, (w+h)/2)
    cv2.imwrite(output_steps_path + r'\rectangles.jpg', gr.draw_rectangles(img, ocr_data))

    # create black image with white points in the edges of the rectangles
    points_img = gr.draw_points(gr.get_black_image(img.shape), rects_points)
    cv2.imwrite(output_steps_path + r'\points_img.jpg', points_img)
    #gr.print_img("all rectangles", gr.draw_rectangles(img, ocr_data))


def filter_by_clusters(rects_points, img_scale):
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



