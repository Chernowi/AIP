from matplotlib import pyplot
import PIL.Image
import numpy as np
from pathlib import Path
import random as rd
import cv2
import os
import matplotlib.pyplot as plt
current_dir = Path.cwd()


def shift(image, max_shift):
    global noise_h, noise_w
    h, w = image.shape
    noise_h = h + max_shift
    noise_w = w + max_shift
    shifted_image = np.zeros(( h + max_shift, w + max_shift))
    x_shift = rd.randint(1, max_shift)
    y_shift = rd.randint(1, max_shift)
    shifted_image[y_shift: h + y_shift, x_shift: w + x_shift] = image
    return shifted_image


def salt_pepper(image, probability):
    h, w = image.shape
    for y in range(h):
        for x in range(w):
            if rd.randint(1, 1000) < probability:
                image[y][x] = 255
                noise_loc.append((y, x))
    return image


def get_noise_ratio(image_name):
    # noise_w and noise_h variables are used to adjust the image with the noise locations
    image = cv2.imread(image_name)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    noise_count = 0
    h, w = gray.shape
    dx = (w - noise_w)//2
    dy = (h - noise_h)//2
    for coordinate in noise_loc:
        y, x = coordinate
        x += dx
        y += dy
        if gray[y][x] == 255:
            noise_count += 1
    if noise_count != 0:
        return (w*h)/noise_count
    else:
        return w*h


def simulate_long_exposure(shifted, noise):
    image = np.max(shifted, axis=0)
    save_im = PIL.Image.fromarray(image)
    save_im = save_im.convert("RGB")
    if noise:
        save_im.save("long_exposure_simulated/long_exposure_with_noise.jpg")
    else:
        save_im.save("long_exposure_simulated/long_exposure_without_noise.jpg")


def get_sharpness(image):
    image = cv2.GaussianBlur(image, (3, 3), 0, 0)
    ksize = 11
    scale = 0.2
    delta = 0
    laplacian = cv2.Laplacian(image, cv2.CV_64F, ksize=ksize, delta=delta, scale=scale)
    _, std = cv2.meanStdDev(laplacian)
    return std[0][0]**2


def generate_simulated(read_im, noise):
    shifted_images = []
    for i in range(10):
        gray = cv2.cvtColor(read_im, cv2.COLOR_BGR2GRAY)
        image = shift(gray, 8)
        if noise:
            image = salt_pepper(image, 2)
            save_im = PIL.Image.fromarray(image)
            save_im = save_im.convert("RGB")
            save_im.save(current_dir / str(str(i) + '.jpg'))
        shifted_images.append(image)
    return shifted_images


def test():
    read_im = cv2.imread("raw/jupiter.jpg")
    h, w, _ = read_im.shape
    shifted_images_noise = generate_simulated(read_im, True)
    shifted_images = generate_simulated(read_im, False)
    simulate_long_exposure(shifted_images_noise, True)
    simulate_long_exposure(shifted_images, False)
    os.system("python3.8 ../../AIP.py")
    corrected_nr = get_noise_ratio("result_images/result.jpg")
    simulated_nr = get_noise_ratio("long_exposure_simulated/long_exposure_with_noise.jpg")
    print("Signal to noise ratio (corrected):", corrected_nr)
    print("Signal to noise ratio (simulated):", simulated_nr)
    return corrected_nr, simulated_nr


corrected_pts = []
simulated_pts = []
noise_loc = []
noise_w = 0
noise_h = 0
n_runs = 1


for i in range(1, n_runs+1):
    corrected_nr, simulated_nr = test()
    noise_loc = []
    corrected_pts.append([i, corrected_nr])
    simulated_pts.append([i, simulated_nr])


plt.scatter(*zip(*simulated_pts), c='r', label="simulated")
plt.scatter(*zip(*corrected_pts), c='b', label="corrected")
plt.legend(loc="upper left")
plt.show()