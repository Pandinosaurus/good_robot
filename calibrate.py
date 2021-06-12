#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import time
import cv2
from real.camera import Camera
from robot import Robot
from scipy import optimize  
from mpl_toolkits.mplot3d import Axes3D  
from tqdm import tqdm

# User options (change me)
# --------------- Setup options ---------------
tcp_host_ip = '192.168.1.155' # IP and port to robot arm as TCP client (UR5)
tcp_port = 30002
rtc_host_ip = '192.168.1.155' # IP and port to robot arm as real-time client (UR5)
rtc_port = 30003
# workspace_limits = np.asarray([[0.3, 0.748], [0.05, 0.4], [-0.2, -0.1]]) # Cols: min max, Rows: x y z (define workspace limits in robot coordinates)
# x_offset = 0.0
# y_offset = -0.4
# workspace_limits = np.asarray([[0.3 + x_offset, 0.748 + x_offset], [0.05 + y_offset, 0.3 + y_offset], [0.15, 0.4]]) # Cols: min max, Rows: x y z (define workspace limits in robot coordinates)
workspace_limits = np.asarray([[0.5, 0.75], [-0.3, 0.1], [0.17, 0.3]]) # Real Good Robot
calib_grid_step = 0.05
# Checkerboard tracking point offset from the tool in the robot coordinate
checkerboard_offset_from_tool = [-0.01, 0.0, 0.108]
tool_orientation = [0, np.pi/2, 0.0] # Real Good Robot

# tool_orientation = [-np.pi/2,0,0] # [0,-2.22,2.22] # [2.22,2.22,0]
# X is the axis from the robot to the clamp with the camera
# Y is the axis from the window to the computer
# Z is the vertical axis

# This orientation is the gripper pointing towards the camera, with the tag up.
# tool_orientation = [0, np.pi/2, 0]
# This orientation is the tag pointing towards the camera (45 degree angle)
# tool_orientation = [0, np.pi/2 + np.pi/4, 0]


# Construct 3D calibration grid across workspace
num_calib_grid_pts, calib_grid_pts = utils.calib_grid_cartesian(workspace_limits, calib_grid_step)

measured_pts = []
observed_pts = []
observed_pix = []

# Move robot to home pose
print('Connecting to robot...')
print('WARNING: Have your STOP button ready! The robot may move suddenly!')
print('WARNING: Be sure to move the bin from in front of the robot!')
robot = Robot(False, None, None, workspace_limits,
              tcp_host_ip, tcp_port, rtc_host_ip, rtc_port,
              False, None, None)
print('Robot active, open the gripper')
robot.open_gripper()
print('Gripper opened!')

# Slow down robot
robot.joint_acc = 1.7
robot.joint_vel = 1.2

# Make robot gripper point upwards
# robot.move_joints([-np.pi, -np.pi/2, np.pi/2, 0, np.pi/2, np.pi])
# The tag is pointing upwards at home
print('MOVING THE ROBOT to home position...')
robot.go_home()

# Move robot to each calibration point in workspace
print('Collecting data...')
for calib_pt_idx in tqdm(range(num_calib_grid_pts)):
    tool_position = calib_grid_pts[calib_pt_idx,:]
    print(' pos: ' + str(tool_position) + ' rot: ' + str(tool_orientation))
    robot.move_to(tool_position, tool_orientation)
    time.sleep(1)
 
    # Find checkerboard center
    checkerboard_size = (3,3)
    refine_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    camera_color_img, camera_depth_img = robot.get_camera_data()
    bgr_color_data = cv2.cvtColor(camera_color_img, cv2.COLOR_RGB2BGR)
    gray_data = cv2.cvtColor(bgr_color_data, cv2.COLOR_RGB2GRAY)
    checkerboard_found, corners = cv2.findChessboardCorners(gray_data, checkerboard_size, None, cv2.CALIB_CB_ADAPTIVE_THRESH)
    
    if checkerboard_found:
        print("Checkerboard found!")
        corners_refined = cv2.cornerSubPix(gray_data, corners, (3,3), (-1,-1), refine_criteria)

        # Get observed checkerboard center 3D point in camera space
        # The point VPG is tracking is the middle one of a (3x3) checkerboard.
        checkerboard_pix = np.round(corners_refined[4,0,:]).astype(int)
        checkerboard_z = camera_depth_img[checkerboard_pix[1]][checkerboard_pix[0]]
        checkerboard_x = np.multiply(checkerboard_pix[0]-robot.cam_intrinsics[0][2],checkerboard_z/robot.cam_intrinsics[0][0])
        checkerboard_y = np.multiply(checkerboard_pix[1]-robot.cam_intrinsics[1][2],checkerboard_z/robot.cam_intrinsics[1][1])
        if checkerboard_z == 0:
            continue

        # Save calibration point and observed checkerboard center
        observed_pts.append([checkerboard_x,checkerboard_y,checkerboard_z])
        # tool_position[2] += checkerboard_offset_from_tool
        tool_position = tool_position + checkerboard_offset_from_tool

        measured_pts.append(tool_position)
        observed_pix.append(checkerboard_pix)

        # Draw and display the corners
        # vis = cv2.drawChessboardCorners(robot.camera.color_data, checkerboard_size, corners_refined, checkerboard_found)
        vis = cv2.drawChessboardCorners(bgr_color_data, (1,1), corners_refined[4,:,:], checkerboard_found)
        cv2.imwrite('%06d.png' % len(measured_pts), vis)
        cv2.imshow('Calibration',vis)
        cv2.waitKey(10)



# Move robot back to home pose
robot.go_home()

measured_pts = np.asarray(measured_pts)  # The measured_pts is in m unit. 
observed_pts = np.asarray(observed_pts) / 1000  # The observed_pts is in mm unit. Changing the unit to m.
observed_pix = np.asarray(observed_pix)
world2camera = np.eye(4)

# Save the collected points
np.savetxt('measured_pts.txt', np.asarray(measured_pts), delimiter=' ')
np.savetxt('observed_pts.txt', np.asarray(observed_pts), delimiter=' ')
np.savetxt('observed_pix.txt', np.asarray(observed_pix), delimiter=' ')


# Estimate rigid transform with SVD (from Nghia Ho)
def get_rigid_transform(A, B):
    assert len(A) == len(B)
    N = A.shape[0]; # Total points
    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)
    AA = A - np.tile(centroid_A, (N, 1)) # Centre the points
    BB = B - np.tile(centroid_B, (N, 1))
    H = np.dot(np.transpose(AA), BB) # Dot is matrix multiplication for array
    U, S, Vt = np.linalg.svd(H)
    R = np.dot(Vt.T, U.T)
    if np.linalg.det(R) < 0: # Special reflection case
       Vt[2,:] *= -1
       R = np.dot(Vt.T, U.T)
    t = np.dot(-R, centroid_A.T) + centroid_B.T
    return R, t

def get_rigid_transform_error(z_scale):
    global measured_pts, observed_pts, observed_pix, world2camera, camera

    # Apply z offset and compute new observed points using camera intrinsics
    observed_z = observed_pts[:,2:] * z_scale
    observed_x = np.multiply(observed_pix[:,[0]]-robot.cam_intrinsics[0][2],observed_z/robot.cam_intrinsics[0][0])
    observed_y = np.multiply(observed_pix[:,[1]]-robot.cam_intrinsics[1][2],observed_z/robot.cam_intrinsics[1][1])
    new_observed_pts = np.concatenate((observed_x, observed_y, observed_z), axis=1)

    # Estimate rigid transform between measured points and new observed points
    R, t = get_rigid_transform(np.asarray(measured_pts), np.asarray(new_observed_pts))
    t.shape = (3,1)
    world2camera = np.concatenate((np.concatenate((R, t), axis=1),np.array([[0, 0, 0, 1]])), axis=0)

    # Compute rigid transform error
    registered_pts = np.dot(R,np.transpose(measured_pts)) + np.tile(t,(1,measured_pts.shape[0]))
    error = np.transpose(registered_pts) - new_observed_pts
    error = np.sum(np.multiply(error,error))
    rmse = np.sqrt(error/measured_pts.shape[0])
    return rmse

# Optimize z scale w.r.t. rigid transform error
print('Calibrating...')
z_scale_init = 1
optim_result = optimize.minimize(get_rigid_transform_error, np.asarray(z_scale_init), method='Nelder-Mead')
camera_depth_offset = optim_result.x

# Save camera optimized offset and camera pose
print('Saving...')
np.savetxt('real/camera_depth_scale.txt', camera_depth_offset, delimiter=' ')
get_rigid_transform_error(camera_depth_offset)
camera_pose = np.linalg.inv(world2camera)
np.savetxt('real/robot_base_to_camera_pose.txt', camera_pose, delimiter=' ')
print('Done.')

# DEBUG CODE -----------------------------------------------------------------------------------

# np.savetxt('measured_pts.txt', np.asarray(measured_pts), delimiter=' ')
# np.savetxt('observed_pts.txt', np.asarray(observed_pts), delimiter=' ')
# np.savetxt('observed_pix.txt', np.asarray(observed_pix), delimiter=' ')
# measured_pts = np.loadtxt('measured_pts.txt', delimiter=' ')
# observed_pts = np.loadtxt('observed_pts.txt', delimiter=' ')
# observed_pix = np.loadtxt('observed_pix.txt', delimiter=' ')

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.scatter(measured_pts[:,0],measured_pts[:,1],measured_pts[:,2], c='blue')

# print(camera_depth_offset)
# R, t = get_rigid_transform(np.asarray(measured_pts), np.asarray(observed_pts))
# t.shape = (3,1)
# camera_pose = np.concatenate((np.concatenate((R, t), axis=1),np.array([[0, 0, 0, 1]])), axis=0)
# camera2robot = np.linalg.inv(camera_pose)
# t_observed_pts = np.transpose(np.dot(camera2robot[0:3,0:3],np.transpose(observed_pts)) + np.tile(camera2robot[0:3,3:],(1,observed_pts.shape[0])))

# ax.scatter(t_observed_pts[:,0],t_observed_pts[:,1],t_observed_pts[:,2], c='red')

# new_observed_pts = observed_pts.copy()
# new_observed_pts[:,2] = new_observed_pts[:,2] * camera_depth_offset[0]
# R, t = get_rigid_transform(np.asarray(measured_pts), np.asarray(new_observed_pts))
# t.shape = (3,1)
# camera_pose = np.concatenate((np.concatenate((R, t), axis=1),np.array([[0, 0, 0, 1]])), axis=0)
# camera2robot = np.linalg.inv(camera_pose)
# t_new_observed_pts = np.transpose(np.dot(camera2robot[0:3,0:3],np.transpose(new_observed_pts)) + np.tile(camera2robot[0:3,3:],(1,new_observed_pts.shape[0])))

# ax.scatter(t_new_observed_pts[:,0],t_new_observed_pts[:,1],t_new_observed_pts[:,2], c='green')

# plt.show()