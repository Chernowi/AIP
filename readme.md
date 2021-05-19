## A solution to atmospheric turbulence aberration in astrophotography using speckle imaging techniques
****
### Contents ###
**1. Introduction**  
**2. How to use**  
**3. The algorithm**  
&nbsp;&nbsp;&nbsp; **3.1. Fetching the images**  
&nbsp;&nbsp;&nbsp; **3.2. Calculating the shift of the images**  
&nbsp;&nbsp;&nbsp; **3.3. Stacking the images**  
**4. Testing**

### 1. Introduction
This project focuses on improving the resolution of telescopes that are limited by atmospheric turbulence. It works 
by stacking short exposure images of an object to form a sharper image with a higher signal-to-noise ratio. 
it can be used both for Narrow and Wide angle observations, provided that the turbulence has only shifted 
(and not deformed or rotated) the observed objects.  


### 2. How to use
The latest working version is [AIP.py](AIP.py), to run the program, execute it with python3.8 while in the directory where the images are
(all the images must have the same dimensions). The arguments you can use are:  
* -p --pivot [filename]   
  Use it to select the image that will be used to compare against the rest, this image will be in the center 
  of the final image. In the absence of this argument the first image will be selected as pivot.
  

* -b --bright [radius]  
  Use it to apply bright-spot correlation mode, you have to provide a positive odd int as radius value.
  In the absence of this argument phase correlation will be used.
  

There are images to try the program inside [Tests](Tests) directory.  

**Example use**  

For example if you are in the directory [Tests/jupiter](Tests/jupiter), you could run the program like this:  
**python3.8 ../../AIP.py -p 3.jpg**

**Output**

The program creates a directory called "result_images". Inside, you will find the result image "result.jpg", and a directory
called "corrected_images", this directory will contain the shift-corrected images that form the stack. 
#### Requirements
The program must be executed with python 3.8.  
The following libraries are required to run the program:  

`shutil` `PIL` `numpy` `fnmatch` `os` `pathlib` `time` `opencv` `argparse` `matplotlib`  

### 3. The algorithm
The program can be divided in three actions: fetching the images, calculating their shift and stacking them. 
Below you will find a description of each action, divided into each of the steps. The code that is shown includes only the
lines that are relevant to explain the algorithm.  
The following code can be found in [AIP.py](AIP.py)
#### 3.1. Fetching the images  

  ```python
  image_filenames = fnmatch.filter(os.listdir(currentDir), "*.jpg")
  if pivot_image_filename in image_filenames:
      pivot_image_index = image_filenames.index(pivot_image_filename)
  else:
      print("Pivot image not found, using first image as pivot")
  images = generate_list_of_images(image_filenames, pivot_image_index)
  ````
1. Fetch all the filenames that end with ".jpg" and are in the working directory.
2. If a valid pivot image has been passed as an argument to the program, its index is found, otherwise the image with index
0 is used as pivot.
 ```python
 def generate_list_of_images(image_filenames, pivot_image_index):
  pivot = cv2.imread(str(currentDir / image_filenames[pivot_image_index]))
  w, h, _ = pivot.shape
  images = []
  for i in range(len(image_filenames)):
      image = cv2.imread(str(currentDir / image_filenames[i]))
      iw, ih, _ = image.shape
      if iw == w and ih == h:
          images.append(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
      else:
          print('Image "' + image_filenames[i] + '" has invalid dimensions and will not be processed')
  return images
 ````

3. The function generate_list_of_images() reads each image and checks if it has the same dimensions as the pivot, then 
it appends them as grayscale images and returns the list.

#### 3.2. Calculating the shift of the images

**Phase correlation**  
The standard way the program calculates the shift is by cross-correlating each image with the pivot image, this is done
with the help of the fast fourier transform algorithm by the function phase_correlation(), shown below.

```python
def phase_correlation(pivot, image):
    G_a = np.fft.fft2(pivot)
    G_b = np.fft.fft2(image)
    conj_b = np.ma.conjugate(G_b)
    R = G_a * conj_b
    R /= np.absolute(R)
    r = np.fft.ifft2(R).real
    blurred_r = cv2.GaussianBlur(r, (5, 5), 0)
    x, y = np.unravel_index(blurred_r.argmax(), blurred_r.shape)
    return x, y
 ````
The equation for the phase correlation is described in [phase_correlation](Documents/phase_correlation/phase_correlation.pdf).  
A blur is applied to the result in order to eliminate false peaks, then, the coordinates of the peak are returned.  

**Bright-spot correlation**  
There is also another way the program can correlate the images, by finding the brightest spot in each image. This is useful
for single star or binary system images where phase correlation does not work well.
```python
def bright_spot_correlation(pivot, image, radius):
    blurred_pivot = cv2.GaussianBlur(pivot, (radius, radius), 0)
    (_, _, _, pivot_loc) = cv2.minMaxLoc(blurred_pivot)
    blurred_image = cv2.GaussianBlur(image, (radius, radius), 0)
    (_, _, _, image_loc) = cv2.minMaxLoc(blurred_image)
    x = pivot_loc[0] - image_loc[0]
    y = pivot_loc[1] - image_loc[1]
    return x, y
 ````
A blur is applied with the specified radius to eliminate bright spots that could result in false positives. Then, the 
coordinates of the brightest spot for each image are subtracted and returned.  

#### 3.3. Stacking the images

After the shift between the image and the pivot is returned, the image is placed in an array of size 2*width X 2 *height,
positioned to correct the shift. A visual example is shown in [image_stacking](Documents/image_stacking/image_stacking.pdf).

```python
h, w = pivot_image.shape
max_horizontal_shift = w // 2
max_vertical_shift = h // 2
base = np.zeros((h + 2 * max_vertical_shift, w + 2 * max_horizontal_shift))

base[max_vertical_shift:h + max_vertical_shift, max_horizontal_shift:w + max_horizontal_shift] = image
 ````

### 4. Testing

The tests and their descriptions can be found inside [Tests](Tests) directory.
