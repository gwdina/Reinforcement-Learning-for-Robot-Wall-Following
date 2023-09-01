#!/usr/bin/python3

import rospy
import cmath
import string
import time
import random
import csv
import json
from gazebo_msgs.srv import GetModelState
from std_srvs.srv import Empty
from geometry_msgs.msg import Twist, Pose
from sensor_msgs.msg import LaserScan
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState
from nav_msgs.msg import Path


# 1(medium), 0(close), 2 (far)

state = [0,0,0]
scanData = None

def callback(data):
     global scanData
     scanData = data.ranges


def getState():
    global state
    global scanData
    state = ["0","0","0"]

     #front
    Fsum = 0 
    for i in range(85,95):
        Fsum += scanData[i]
        #print(scanData[i])
        

    Favg = Fsum/10

    if (Favg > 1):
        state[0] = '2'
    else:
        state[0] = '0'

    #Angle
    Asum = 0 
    for i in range(40,70):
        Asum += scanData[i]
        #print(scanData[i])

    Aavg = Asum/30

    if (Aavg > 1):
        state[1] = '2'
    elif ((Aavg < .7) and (Aavg > .4)):
        state[1] = '1'
    else:
        state[1] = '0' 

    #Right
    Rsum = 0 
    for i in range(0,10):
        Rsum  += scanData[i]
        #print(scanData[i])

    Ravg = Rsum/10

    if (Ravg > 1):
        state[2] = '2'
    elif ((Ravg < .7) and (Ravg > .3)): #.6-.3
        state[2] = '1'
    else:
        state[2] = '0' 
    
    state="".join(state)
    print(state)

def getposition(data):
    global poses
    poses = data.poses



rospy.init_node('laser_scan_publisher')
scan_subscriber = rospy.Subscriber('/scan', LaserScan, callback)
rate = rospy.Rate(2)

velocity_publisher = rospy.Publisher('/triton_lidar/vel_cmd', Twist, queue_size=10)
vel_msg = Twist()




#rospy.wait_for_service('/gazebo/reset_world')
reset_world = rospy.ServiceProxy('/gazebo/reset_world', Empty)
#reset_world()

QTable = {}
with open("Q.txt", "r") as data:
    QTable = json.load(data)


# epsilon = Startingepsilon*d^n(current episode), .9*.0985^180



# actions: follow wall, rotate to face wall when dealing with corners, rotate and move when dealing with 'L' shape

while scanData is None:    
    pass

#
reset_world()

# state_msg = ModelState()
# state_msg.model_name = 'triton_lidar'
# state_msg.pose.position.x = random.uniform(-3.8, 3.8)
# state_msg.pose.position.y = random.uniform(-3.8, 3.8)
# state_msg.pose.position.z = 0
# state_msg.pose.orientation.x = 0
# state_msg.pose.orientation.y = 0
# state_msg.pose.orientation.z = random.uniform(0,2*3.14)
# state_msg.pose.orientation.w = random.uniform(0,2*3.14)
# set_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
# resp = set_state( state_msg )

while not rospy.is_shutdown():

    vel_msg.linear.z = 0
    vel_msg.linear.y = 0
    vel_msg.angular.z = 0
    velocity_publisher.publish(vel_msg)
    getState()

    # one to move foward, one to move foward and left, and one to move foward and right
    # foward
    if (QTable[state].index(max(QTable[state])) == 0):
     #print("Foward "+state)
     vel_msg.linear.y = .25
     vel_msg.angular.z = 0
     vel_msg.linear.z = 0
     velocity_publisher.publish(vel_msg)
    
     

    #foward right
    if (QTable[state].index(max(QTable[state])) == 1):
     #print("right "+state)
     vel_msg.linear.y = 0.25
     vel_msg.angular.z = -0.25
     vel_msg.linear.z = 0
     velocity_publisher.publish(vel_msg)



    #foward left
    if (QTable[state].index(max(QTable[state])) == 2):
     #print("left "+state)
     vel_msg.linear.y = 0.25
     vel_msg.angular.z = 0.25
     vel_msg.linear.z = 0
     velocity_publisher.publish(vel_msg)

    rate.sleep()