import os
import image_aligner
import numpy as np
import cv2


IMG_PATH = r'D:\visual_studio_projects\Aligner\my_data\hobbit_splited\page111.jpg'
IMG_RES_PATH = r'D:\visual studio projects\Aligner\my_data\hobbit_splited\page0_result.jpg'

mask = np.zeros((800, 900, 1), dtype = "uint8")

cv2.imshow("black", mask)
cv2.waitKey(0)

mask = cv2.fillConvexPoly(mask, np.array([[300,100], [300, 600], [800, 1000], [800, 100]]), (255, 255, 255))

cv2.imshow("black", mask)
cv2.waitKey(0)

#mask = cv2.fillConvexPoly(mask, [top_left, bottom_left, bottom_right, top_right], (255, 255, 255))