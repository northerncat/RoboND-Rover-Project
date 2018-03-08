import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Segment image into three components, ground (B), rock (G) and non-navigable (R) using
# color thresholding.
# Ground color should be above certain level, while rocks are golden so a combination of
# high red and green with low blue channel values would identify rocks.
def segment_image(img):
    # ground thresholding using lower bounds
    ground_threshold = (175, 175, 175)
    segmented_image = np.zeros_like(img)
    ground_mask = color_thresh(img, ground_threshold)
    # rock thresholding using lower bounds on RG and upper bounds on the blue channel
    rock_threshold = (120, 120, 60)
    rock_mask = np.zeros_like(ground_mask)
    rock_mask[(img[:,:,0] > rock_threshold[0]) & (img[:,:,1] > rock_threshold[1]) & (img[:,:,2] < rock_threshold[2])] = 1
    # place non-ground pixels in R
    segmented_image[:,:,0] = 255 * np.logical_not(ground_mask)
    # place rock mask in G
    segmented_image[:,:,1] = 255 * (rock_mask & np.logical_not(ground_mask))
    # place ground pixels in B
    segmented_image[:,:,2] = 255 * ground_mask
    return segmented_image

# Gets a set of predefined sources and desinations with its corresponding scale for
# perspective transform
def get_predefined_src_dst(img):
    dst_size = 5
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[img.shape[1]/2 - dst_size, img.shape[0] - bottom_offset],
                      [img.shape[1]/2 + dst_size, img.shape[0] - bottom_offset],
                      [img.shape[1]/2 + dst_size, img.shape[0] - 2*dst_size - bottom_offset], 
                      [img.shape[1]/2 - dst_size, img.shape[0] - 2*dst_size - bottom_offset],
                  ])
    scale = 10.0
    return source, destination, scale


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # get the predefined set of source and destinations based on the Rover img size
    src, dst, scale = get_predefined_src_dst(Rover.img)
    # segment the image into channels of ground, rock and obstacle, and transform it
    segmented_image = perspect_transform(segment_image(Rover.img), src, dst)

    # extract information from the Rover
    xpos = Rover.pos[0]
    ypos = Rover.pos[1]
    yaw = Rover.yaw
    world_size = Rover.worldmap.shape[0]

    # store the segmentation results in vision_image and add to the mapping in worldmap
    for ch in range(3):
        # get segmentation of the channel
        segment = segmented_image[:,:,ch]
        # display by storing into vision_image
        Rover.vision_image[:, :, ch] = segment
        # convert segment to world coordinates
        rover_x, rover_y = rover_coords(segment)
        world_x, world_y = pix_to_world(rover_x, rover_y, xpos, ypos, yaw, world_size, scale)
        # increment the worldmap's corresponding channel by 10.0
        Rover.worldmap[world_y, world_x, ch] = Rover.worldmap[world_y, world_x, ch] + 10.0

    # calculate the navigation distances and angles as the ground pixels
    xpix, ypix = rover_coords(segmented_image[:,:,2])
    dist, angles = to_polar_coords(xpix, ypix)
    mean_dir = np.mean(angles)
    Rover.nav_dists = dist
    Rover.nav_angles = angles

    return Rover