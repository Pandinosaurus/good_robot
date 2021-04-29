from robot import Robot
import numpy as np
import time

# This grasp position results in an elbow down grasp, we need to fix that.
# Training iteration: 7
# Change detected: True (value: 485)
# Primitive confidence scores: 2.547277 (push), 3.074675 (grasp)
# Strategy: exploit (exploration probability: 0.499400)
# Action: grasp at (14, 19, 2)
# Executing: grasp at (0.380000, -0.226000, -0.040000)
# Grasp position before applying workspace bounds: [ 0.38  -0.226  0.11 ]
# ('Real Good Robot grasping at: [ 0.38  -0.226  0.15 ]', ', [ 2.90245315 -1.20223546  0.        ]')
# Trainer.get_label_value(): Current reward: 0.000000 Current reward multiplier: 1.000000 Predicted Future reward: 3.074675 Expected reward: 0.000000 + 0.500000 x 3.074675 = 1.537337

# Here is another grasp which went to elbow down:
# Change detected: False (value: 144)
# Trainer.get_label_value(): Current reward: 0.000000 Current reward multiplier: 1.000000 Predicted Future reward: 0.000000 Expected reward: 0.000000 + 0.500000 x 0.000000 = 0.000000
# Primitive confidence scores: 3.739099 (push), 2.467160 (grasp)
# Strategy: explore (exploration probability: 0.499001)
# Action: grasp at (14, 19, 2)
# Training loss: 0.000447
# Executing: grasp at (0.380000, -0.226000, -0.040000) orientation: 5.497787
# Grasp position before applying workspace bounds: [ 0.38  -0.226  0.11 ]
# ('Real Good Robot grasping at: [ 0.38  -0.226  0.15 ]', ', [ 2.90245315 -1.20223546  0.        ]')



# This is a grasp motion which hits the joint limits:                    
# Training iteration: 3                                                                                                                                    
# Change detected: False (value: 22)                                                                                             
# Trainer.get_label_value(): Current reward: 0.000000 Current reward multiplier: 1.000000 Predicted Future reward: 0.000000 Expected reward: 0.000000 + 0.50
# 0000 x 0.000000 = 0.000000                                                                                                     
# Primitive confidence scores: 2.997465 (push), 2.999384 (grasp)                                                                 
# Strategy: explore (exploration probability: 0.499800)                                                                          
# Action: grasp at (4, 120, 220)                                                          
# Training loss: 3.493566                                                                                                        
# Experience Replay: We do not have samples for the push action with a success state of True, so sampling from the whole history.
# Executing: grasp at (0.816000, -0.024000, -0.040000) orientation: 1.570796                                                     
# Grasp position before applying workspace bounds: [ 0.816 -0.024  0.11 ]                                                        
# ('Real Good Robot grasping at: [ 0.816 -0.024  0.15 ]', ', [2.22144147 2.22144147 0.        ]')    

i = 0
r = Robot(is_sim=False, tcp_host_ip='192.168.1.155', tcp_port=30002, place=False)

# print('Robot cartesian home: ' + str(r.get_cartesian_position()))
# r.move_to([0.4387914740866465, -0.02251891154755168, 0.6275728717960743], None)
# r.move_to([0.4387914740866465, -0.02251891154755168, 0.3275728717960743], None)

# tool_orientation = [0.0, 0.0, 0.0] # Real Good Robot
# above_bin_waypoint = [0.3, 0.0,  0.8]
# r.move_to(above_bin_waypoint, tool_orientation)r.grasp([0.414000, -0.092000, 0.103734], 0.0)
# r.grasp([0.818000, -0.226000, 0.003854], 3.141593)


# The test gripper functionality loop 
# closes the gripper 5 times in a row,
# then opens the gripper. This allows
# you to test and check the gripper's
# built in object detection functionality
test_gripper_functionality = False
while test_gripper_functionality:
    i += 1
    # Loop to 
    stat1 = r.close_gripper()
    time.sleep(1.0)
    stat2 = r.close_gripper()
    time.sleep(1.0)
    stat3 = r.close_gripper()
    time.sleep(1.0)
    stat4 = r.close_gripper()
    stat5 = r.open_gripper()
    print('i: ' + str(i) + ' close1: ' + str(stat1) + ' close2: ' + str(stat2) + ' close3: ' + str(stat3) + ' close4: ' + str(stat4) + ' open5: ' + str(stat3))

# r.grasp([0.414000, -0.092000, 0.003734], 0.0)
# r.place([0.414000, -0.092000, 0.003734], 0.0)
# # r.push([0.414000, -0.092000, 0.003734], 0.0)

# r.grasp([0.816000, -0.024000, -0.040000], 1.570796)
retry_grasp = True
while retry_grasp:
    r.grasp([0.380000, -0.226000, -0.040000], 5.497787)

print_robot_pose = True
while print_robot_pose:
    # Loop and print current position so you can use that data
    # for updating and configuring the robot.
    state_data = r.get_state()
    actual_tool_pose = r.parse_tcp_state_data(state_data, 'cartesian_info')
    joint_position = r.parse_tcp_state_data(state_data, 'joint_data')
    robot_state = 'cart_pose: ' + str(actual_tool_pose) + ' joint pos: ' + str(joint_position)
    print(robot_state)
    time.sleep(1.0)

# Action: grasp at (8, 19, 221)
# Executing: grasp at (0.818000, -0.226000, 0.003854) orientation: 3.141593
# Grasp position before applying workspace bounds: [ 0.818      -0.226       0.14385387]
# Real Good Robot grasping at: [ 0.818 -0.226  0.15 ], [1.92367069e-16 3.14159265e+00 0.00000000e+00]

# time.sleep(.1)
# Training iteration: 1
# Change detected: True (value: 972)
# Primitive confidence scores: 3.698842 (push), 3.391453 (grasp)
# Strategy: exploit (exploration probability: 0.500000)
# Action: push at (0, 86, 19)
# Real Robot push at (0.414000, -0.092000, 0.003734) angle: 0.000000
# Gripper finished moving!
# Trainer.get_label_value(): Current reward: 1.000000 Current reward multiplier: 1.000000 Predicted Future reward: 3.698842 Expected reward: 1.000000 + 0.500000 x 3.698842 = 2.849421
# Training loss: 0.984293


# tool_pos = [0.6, -0.1, 0.4]
# tool_orientation = [0.0, np.pi, 0.0]
# r.move_to(tool_pos, tool_orientation)

# grasp_orientation = [1, 0]
# tool_rotation_angle = np.pi/2 / 2
# tool_orientation = np.asarray([grasp_orientation[0]*np.cos(tool_rotation_angle) - grasp_orientation[1]*np.sin(tool_rotation_angle), grasp_orientation[0]*np.sin(tool_rotation_angle) + grasp_orientation[1]*np.cos(tool_rotation_angle), 0.0])*np.pi
# print(tool_orientation)
# r.move_to(tool_pos, tool_orientation)

# tool_orientation = [np.pi/2, np.pi/2, 0.0]
# r.move_to(tool_pos, tool_orientation)