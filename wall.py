#!/usr/bin/python3

import rospy
import cmath
import string
import time
import random
import csv
import json
from gazebo_msgs.srv import GetModelState, GetModelStateRequest, SetModelState
from std_srvs.srv import Empty
from geometry_msgs.msg import Twist, Pose
from sensor_msgs.msg import LaserScan
from gazebo_msgs.msg import ModelState
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
    #print(state)

poses = None
def getposition(data):
    global poses
    poses = data.poses
    

def loc():
    global poses
    x = 0
    y = 0
    for i in range(-4,0,1):
        x += abs(poses[i].pose.position.x-poses[i-1].pose.position.x)
        y += abs(poses[i].pose.position.y-poses[i-1].pose.position.y)
    return x<0.01 and y<0.01

rospy.init_node('laser_scan_publisher')
scan_subscriber = rospy.Subscriber('/scan', LaserScan, callback)
rate = rospy.Rate(2)

location = rospy.Subscriber('/triton/path', Path, getposition)

velocity_publisher = rospy.Publisher('/triton_lidar/vel_cmd', Twist, queue_size=10)
vel_msg = Twist()


model_coordinates = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
object_coords = model_coordinates("triton_lidar", "")


#rospy.wait_for_service('/gazebo/reset_world')
reset_world = rospy.ServiceProxy('/gazebo/reset_world', Empty)
reset_world()


QTable = {}

lr = 0.2 # learning rate
ds = 0.8 # discount factor 
episodes = 201 # n episode

decay = .985

# epsilon = Startingepsilon*d^n(current episode), .9*.0985^180


# actions: follow wall, rotate to face wall when dealing with corners, rotate and move when dealing with 'L' shape

while scanData is None:    
    pass
while poses is None:    
    pass


def get_action(epsilon):
    ran = random.uniform(0, 1)


    #
    if (ran > epsilon):
            #deal with all zeros/ties
            
            if (max(QTable[state]) == 0):
                current_action = random.randint(0,2)
            else:
                current_action = QTable[state].index(max(QTable[state]))


    # random action 
    else:
        current_action = random.randint(0,2)

    return current_action

def action_run(action):

    # one to move foward, one to move foward and left, and one to move foward and right
    # foward
    #2
    # if (action==2):
    #  #print("Foward "+state)
    #  vel_msg.linear.y = .25
    #  vel_msg.angular.z = 0
    #  vel_msg.linear.z = 0
    #  velocity_publisher.publish(vel_msg)
    
     
    # #1
    # #foward right
    # if (action==1):
    #  #print("right "+state)
    #  vel_msg.linear.y = 0.25
    #  vel_msg.angular.z = -0.25
    #  vel_msg.linear.z = 0
    #  velocity_publisher.publish(vel_msg)



    # #foward left
    # #0
    # if (action==0):
    #  #print("left "+state)
    #  vel_msg.linear.y = 0.25
    #  vel_msg.angular.z = 0.25
    #  vel_msg.linear.z = 0
    #  velocity_publisher.publish(vel_msg)

    if (action==0):
     #print("Foward "+state)
     vel_msg.linear.y = .25
     vel_msg.angular.z = 0
     vel_msg.linear.z = 0
     velocity_publisher.publish(vel_msg)
    
     
    #1
    #foward right
    if (action==1):
     #print("right "+state)
     vel_msg.linear.y = 0.25
     vel_msg.angular.z = -0.25
     vel_msg.linear.z = 0
     velocity_publisher.publish(vel_msg)



    #foward left
    #0
    if (action==2):
     #print("left "+state)
     vel_msg.linear.y = 0.25
     vel_msg.angular.z = 0.25
     vel_msg.linear.z = 0
     velocity_publisher.publish(vel_msg)

     rate.sleep()


state_msg = ModelState()
state_msg.model_name = 'triton_lidar'



while not rospy.is_shutdown():
    for e in range(episodes):
        print(e)
        reset_world()
        rate.sleep()
        #reward = 0.0
        
        state_msg.pose.position.x = random.uniform(-3.8, 3.8)
        state_msg.pose.position.y = random.uniform(-3.8, 3.8)
        state_msg.pose.position.z = 0
        state_msg.pose.orientation.x = 0
        state_msg.pose.orientation.y = 0
        state_msg.pose.orientation.z = random.uniform(0,2*3.14)
        state_msg.pose.orientation.w = random.uniform(0,2*3.14)
        set_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
        resp = set_state( state_msg )


        vel_msg.linear.z = 0
        vel_msg.linear.y = 0
        vel_msg.angular.z = 0
        velocity_publisher.publish(vel_msg)

        ep = .9*(decay**e)
        for iter in range(1000):
                if(state_msg.pose.position.z > 0):
                    print("I tried to fly")
                    break
                if(vel_msg.linear.z > 0):
                    print("I tried to fly")
                    break
                reward = 0.0
                getState()
                if(state_msg.pose.position.z > 0):
                    print("I tried to fly")
                    break
                if(vel_msg.linear.z > 0):
                    print("I tried to fly")
                    break


                # ep = .9*(decay**e)
                if not(state in QTable.keys()):
                        QTable[state] = [0,0,0]
                
                current_action = get_action(ep) # choose action based on current state

                action_run(current_action) # execute action

                old_state = state
                getState()
                if not(state in QTable.keys()):
                        QTable[state] = [0,0,0]
                

                 #(0/2),(0/1/2),(0/1/2)   

                # if (state[0] == "0"):
                #     reward += .5

                # if (state[1] == "0"):
                #     reward += -3
                # elif (state[1] == "2"):
                #     reward += -.5
                # elif (state[1] == "1"):
                #     reward += 2
                
                

                # if (state[2] == "0"):
                #     reward += -5
                # elif (state[2] == "1"):
                #     reward += 2

                # elif (state[2] == "2"):
                #     reward += -.5

                # else:
                #     reward += 1
    


                if((state[2] == "2") or (state[1] == "2")):
                    reward -= .5
                if((state[2] == "0") or (state[1] == "0")):
                    reward -= 3

                if((state[2] == "1") or (state[1] == "1")):
                    reward += 2

                if(state[0] == 2):
                    reward += 0
                if(state[0] == 0):
                    reward += 1

                # print(reward)


                # epsilon = Startingepsilon*d^n(current episode), .9*.0985^1e
                # epsilon = .9*(decay**e)
                
                QTable[old_state][current_action] = QTable[old_state][current_action] + lr*(reward + ds * max(QTable[state]) - QTable[old_state][current_action])
                
                #update Q table: Qnew(st,at) = Qold(st,at) + lr * (reward + ds * maxQ(st+1,a) - Qold(st,at))
                # check termination: perfect, stuck and flying
                # if(loc()):
                #     print("I got stuck")
                #     break
                # if(stuck(LastX, LastY)):
                #     print("I got stuck")
                #     break
                # if(object_coords.pose.position.z > 0):
                #     print("I tried to fly")
                #     break
                if(state_msg.pose.position.z > 0):
                    print("I tried to fly")
                    break
                if(vel_msg.linear.z > 0):
                    print("I tried to fly")
                    break

                # collision
                if(loc()):
                    print("I got stuck")
                    break
                if(iter == 999):
                    print("I did a lot")
                    break
                
                    
        if (e%10 == 0):
            with open("Q.txt", "w") as fp:
                json.dump(QTable, fp) 
    if (e == 200):
        break   

    rate.sleep()

