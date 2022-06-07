import shutil
import sys
import os
from pdf2image import convert_from_path
from fpdf import FPDF
from PIL import Image
import time
import multiprocessing
from multiprocessing import Pool
import re


def main():

    input_pdf_path = ""
    output_dir_path = ""

    # check if there are arguments
    arg_num = len(sys.argv)
    if arg_num == 2:  # script name, input pdf path
        input_pdf_path = sys.argv[1]
        output_pdf_path = input_pdf_path[:input_pdf_path.rfind('.')] + ' - aligned.pdf'
        output_dir_path = input_pdf_path[:input_pdf_path.rfind('.')] + ' - pages'
    elif arg_num == 3:  # script name, input pdf path, output dir path
        input_pdf_path = sys.argv[1]
        output_pdf_path = input_pdf_path[:input_pdf_path.rfind('.')] + ' - aligned.pdf'  # TODO: think what to do here - where to put output pdf
        output_dir_path = sys.argv[2]

    if not os.path.exists(input_pdf_path):
        print("pdf file not found...")
        return

    if os.path.exists(output_dir_path):
        shutil.rmtree(output_dir_path)
    os.mkdir(output_dir_path)

    # converting pdf file to images
    begin_converting_to_jpg = time.time()
    pages = convert_from_path(input_pdf_path, thread_count=multiprocessing.cpu_count(), dpi=200)
    print("converting pdf to jpgs...")
    for i in range(len(pages)):
        pages[i].save((output_dir_path + r'\page%s.jpg') % i)
    end_converting_to_jpg = time.time()
    print("time for conversion to jpgs: " + get_time_string(end_converting_to_jpg - begin_converting_to_jpg))

    # aligning each image, paralleled
    begin_aligning = time.time()
    print("start aligning...")
    img_pathes = [output_dir_path + "\\" + local_path for local_path in os.listdir(output_dir_path)]
    with Pool() as p:
        p.map(one_image_aligning, img_pathes)
    print("finished Aligning the whole book!")
    end_aligning = time.time()
    print("time for aligning images: " + get_time_string(end_aligning - begin_aligning))

    # merging back into pdf
    begin_merging = time.time()
    to_merge_list = []
    for file_name in os.listdir(output_dir_path):
        if file_name.split('.')[0].endswith("_aligned"):
            to_merge_list.append(file_name)

    # sort images by page number
    to_merge_list = sorted(to_merge_list, key=lambda f: int(f.split('_')[0][4:]))

    imgs = [Image.open(output_dir_path + '\\' + path) for path in to_merge_list]
    imgs = [img.convert('RGB') for img in imgs]
    imgs[0].save(output_pdf_path, save_all=True, append_images=imgs[1:])
    print("pdf file created!")
    end_merging = time.time()
    print("time for merging to pdf: " + get_time_string(end_merging - begin_merging))
    print("total time: " + get_time_string(end_merging - begin_converting_to_jpg))


def get_time_string(t):
    if t < 60:
        return str(round(t, 3)) + " seconds"
    else:
        return str(int(t // 60)) + " minutes, " + str(round(t % 60, 3)) + " seconds"


def one_image_aligning(img_path, img_res_path=""):
    if os.path.exists(img_path):
        if img_res_path == "" or not os.path.exists(img_res_path):
            img_res_path = img_path[:img_path.rfind('.')] + '_aligned.jpg'
        # activating the aligner
        os.system("python image_aligner.py \"" + img_path + "\" \"" + img_res_path + "\"")

        m = re.search(r'\d+$', img_path[img_path.rfind('\\'):img_path.rfind('.')])
        print("Aligning page " + m.group() + " is finished")
        return True
    else:
        return False


if __name__ == "__main__":
    main()
