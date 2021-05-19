#!/usr/bin/env python3
import shutil
import PIL.Image
import numpy as np
import fnmatch
import os
from pathlib import Path
import time
import cv2
import argparse
import matplotlib.pyplot as plt


def generate_list_of_images(image_filenames, pivot_image_index):
    # Returns a list of grayscale image arrays, excluding the images with dimensions different to the pivot image
    pivot = cv2.imread(str(current_dir / image_filenames[pivot_image_index]))
    h, w, _ = pivot.shape
    images = []
    for i in range(len(image_filenames)):
        image = cv2.imread(str(current_dir / image_filenames[i]))
        ih, iw, _ = image.shape
        if iw == w and ih == h:
            images.append(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        else:
            print('Image "' + image_filenames[i] + '" has invalid dimensions and will not be processed')
    return images


def phase_correlation(pivot, image):
    # Returns the peak location of the phase correlation between the two images
    G_a = np.fft.fft2(pivot)
    G_b = np.fft.fft2(image)
    conj_b = np.ma.conjugate(G_b)
    R = G_a * conj_b
    R /= np.absolute(R)
    r = np.fft.ifft2(R).real
    blurred_r = cv2.GaussianBlur(r, (5, 5), 0)
    # plt.imshow(blurred_r)
    # plt.show()
    y, x = np.unravel_index(blurred_r.argmax(), blurred_r.shape)
    return x, y


def bright_spot_correlation(pivot, image, radius):
    # Finds the brightest spot for each image and returns the difference between its locations
    blurred_pivot = cv2.GaussianBlur(pivot, (radius, radius), 0)
    (_, _, _, pivot_loc) = cv2.minMaxLoc(blurred_pivot)
    blurred_image = cv2.GaussianBlur(image, (radius, radius), 0)
    (_, _, _, image_loc) = cv2.minMaxLoc(blurred_image)
    x = pivot_loc[0] - image_loc[0]
    y = pivot_loc[1] - image_loc[1]
    return x, y


def create_directories():
    # Creates the directories where the produced images will be saved
    if os.path.exists(current_dir / 'result_images'):
        shutil.rmtree(current_dir / 'result_images')
    if os.path.exists(current_dir / 'result_images/corrected_images'):
        shutil.rmtree(current_dir / 'result_images/corrected_images')
    os.mkdir(current_dir / 'result_images')
    os.mkdir(current_dir / 'result_images/corrected_images')


def save_image(image, directory, name):
    saveimage = PIL.Image.fromarray(image)
    if saveimage.mode != 'RGB':
        saveimage = saveimage.convert('RGB')
    if isinstance(name, int):
        name = str(name)
    name += ".jpg"
    saveimage.save(current_dir / directory / name)


def using_bright():
    # Check if flag -b has been used
    if args["bright"] is None:
        print("Using phase correlation")
        return False
    else:
        print("Using bright spot correlation")
        return True


def get_radius_arg():
    # Return the radius value from argument -b
    radius = int(args["bright"])
    if radius % 2 != 0:
        return radius
    else:
        raise Exception("Invalid radius argument, must be odd")


def stack_images(pivot_image_filename):
    # Get the filenames of the .jpg pictures inside the same directory
    image_filenames = sorted(fnmatch.filter(os.listdir(current_dir), '*.jpg'))

    # Check if there is more than 1 image in the directory
    if len(image_filenames) < 2:
        raise Exception("Not enough images to process")

    image_stack = []
    pivot_image_index = 0

    # Check if the pivot image exists inside the directory
    if pivot_image_filename in image_filenames:
        pivot_image_index = image_filenames.index(pivot_image_filename)
    else:
        print("Pivot image not found, using first image as pivot")

    images = generate_list_of_images(image_filenames, pivot_image_index)
    pivot_image = images[pivot_image_index]

    # Delete pivot image from the list of images to avoid auto-correlation
    del images[pivot_image_index]

    # Create the base array
    h, w = pivot_image.shape
    max_horizontal_shift = w // 2
    max_vertical_shift = h // 2

    base = np.zeros((h + 2 * max_vertical_shift, w + 2 * max_horizontal_shift))

    # Add the pivot image to the base array, centered
    base[max_vertical_shift:h + max_vertical_shift, max_horizontal_shift:w + max_horizontal_shift] = pivot_image

    save_image(base, 'result_images/corrected_images', 1)

    # Add the base with the pivot image to the image_stack
    image_stack.append(base)

    bright = using_bright()
    if bright:
        radius = get_radius_arg()

    i = 2
    for next_image in images:
        if bright:
            # Unpack the return of bright_spot_correlation into x and y
            x, y = bright_spot_correlation(pivot_image, next_image, radius)
        else:
            # Unpack the return of phase_correlation into x and y
            x, y = phase_correlation(pivot_image, next_image)

        if x > max_horizontal_shift:
            x = x - w
        if y > max_vertical_shift:
            y = y - h

        base = np.zeros((h + 2 * max_vertical_shift, w + 2 * max_horizontal_shift))
        # Add the image to the base array, shift-corrected

        base[max_vertical_shift + y:h + max_vertical_shift + y, max_horizontal_shift + x:w + max_horizontal_shift + x] = next_image

        save_image(base, 'result_images/corrected_images', i)

        # Add the base with the image to the image_stack
        image_stack.append(base)

        print("Corrected image (" + str(i-1) + "/" + str(len(images)) + ")")
        print("Shift (x,y): " + str(x) + "," + str(y))
        i += 1

    # Combine the image_stack of images into an array
    print("Generating combined image...")
    result_array = np.median(image_stack, axis=0)
    save_image(result_array, "result_images", "result")


start_time = time.time()
current_dir = Path.cwd()
create_directories()
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pivot", help="name of the pivot image")
ap.add_argument("-b", "--bright", help="use bright spot correlation, must be followed by the radius value, "
                                       "which cannot be an even number")
args = vars(ap.parse_args())

try:
    stack_images(args["pivot"])
    print("done")
    print("Time taken: " + str(round(time.time() - start_time, 2)) + " seconds")
except Exception as e:
    print(e)
