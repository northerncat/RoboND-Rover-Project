## Project: Search and Sample Return

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./misc/rover_image.jpg
[image2]: ./calibration_images/example_grid1.jpg
[image3]: ./calibration_images/example_rock1.jpg 

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

#### Answer:
- Added in a function `segment_image()` to detect obstacles, rock and ground and combine the three segmentation images to different RGB channels in a single image.
- - Ground detection is using the provided lower bound color thresholding function, with tuned parameters for better false negatives.
- - Obstacles detection is simply the inverse of the ground detection results.
- - Rock detection uses the fact that the rocks are golden, which results in high red and green channel values and low blue channel values. This means if a primitive rock detection can be done by lower bound thresholding on the R and G channel, with upper bound thresholding on the B channel.

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 

#### Answer:
- - For `process_image`, I simply add the segmented image to the video's bottom right. For the world map, I add the segmented images to the world map, incrementing each channel by 10 for one detection results. At the end of each frame, if the count for obstacle detection is higher than that of the ground detection, the ground detection result is discarded.
- - The resulting movie is as attached in output/test_mapping.mp4. Note that since the movie is rendered with a sequence of images I captured using the training mode, the script would not run right away because it'll look for the directory `my_training` on the same level as the `test_dataset`. However, changing the path to `test_dataset` should allow the scripts to run smoothly.

### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

#### Answer:
- - As a first pass, I only modified `perception_step()` to include the image segmentation function as implemented in the test notebook. The ground detection pixels after perspective transformation are used as the navigation angles to determine the steering angle.

#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

I ran the simulator a few times with resolution 1024x768 and good graphics quality on my MacBook Pro. The FPS is usually around 24-26.

It appears that the fidelity decreased to around 60% when the mapping percentage increased to 40%. The fidelity decrease is usually worse when the robot has to turn around after hitting the end of a path. In addition, the fidelity takes a toll when the robot is wobbling due to constantly shifting steering angles.

I tried tuning the parameters of the color thresholding a little bit - increasing the color threshold for ground detection can increase the fidelity but decrease the mapping percentage. I believe the ground detection can be made better by using gradients and/or robust edge detection as opposed to raw color thresholding.

I also found that the robot would be stuck in infinite loops in several places in the simulation. In particular, it would go in circle in the large area on the right of the map, and sometimes in the center. I believe the reason is that the navigation angles are always steering the robot towards the center of a large area, thus making it move in a circle.

Last but not least, it did seem like the robot can always identify the rock samples when encountered.

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

Here I'll talk about the approach I took, what techniques I used, what worked and why, where the pipeline might fail and how I might improve it if I were going to pursue this project further.  

