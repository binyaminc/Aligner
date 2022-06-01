import os
import image_aligner
import numpy as np
import cv2


IMG_PATH = r'D:\visual_studio_projects\Aligner\my_data\hobbit_splited\page111.jpg'
IMG_RES_PATH = r'D:\visual studio projects\Aligner\my_data\hobbit_splited\page0_result.jpg'

img = cv2.imread(IMG_PATH, cv2.IMREAD_GRAYSCALE)
cv2.imshow("img", img)
cv2.waitKey(0)
black_img = np.zeros((img.shape[0], img.shape[1], 1), dtype="uint8")
cv2.imwrite(r'D:\visual_studio_projects\Aligner\my_data\image_results\mask_img.jpg', black_img)
