#!/usr/bin/env python3
from __future__ import print_function

import time
import numpy as np
import robobo
import cv2
import sys
import signal
import random
import prey
import statistics



def terminate_program(signal_number, frame):
    print("Ctrl-C received, terminating program")
    sys.exit(1)



#evolutionair algoritme, waarbij je x keuzes hebt die je eigenlijk in laat vullen dus:
# je hebt 8 sensoren, en bij elk van deze sensoren ga je bij een afstand van x[1]...x[8] 
# de snelheid aanpassen van linkerband naar  x[1][1]...x[8][1] en rechterband naar x[1][2]....x[8][2]
# voor een duur van x[1][3]....x[1][8]
#fitness kan je dan zien als gem nelheid-aantal bumps-gem afstand tot obstakel of zoiets.
#gem snelheid is bijv de max van links/rechts * tijdsduur van actie)/totale tijdsduur gesomd voor elke run
#bumps is aantal keer dat afstand van een ir onder de 0.03
#gem afstand tot obstakel is best lastig aangezien je dit moet minimizen en je ook een false of 0 als meting hebt
# wanneer het juist goed is. Dus iets van: som van 1-waarde waarbij false en 0 een 1 als waarde hebben


def main():

    #3 choices, e.g. weak turn, medium turn, strong turn

    min_speed = -100
    max_speed = 100
    min_distance = 0
    max_distance = 0.3
    min_speed_length = 5
    max_speed_length = 100
    agents = 10
   
    values = []
    random_distance_values = []
    random_speed_left_values = []
    random_speed_right_values = []
    random_speed_length_values = []
    

    # just adding one good working robot
    nested = []
    for j in range (8):
            combine = []
            if (j == 6) | (j == 7):
                random_distance = [0.08,0.15,0.25]
                random_speed_left = [30,25,20]
                random_speed_right = [-30,0,8]
                random_speed_length = [10,10,10]
            elif (j == 3) | (j == 4):
                random_distance = [0.08,0.15,0.25]
                random_speed_left = [-30,0,8]
                random_speed_right = [30,25,20]
                random_speed_length = [10,10,10]
            else:

                random_distance = np.random.uniform(low=0, high=0, size=(3,))
                random_distance.sort()
                random_speed_left = np.random.uniform(low=0, high=0, size=(3,))
                random_speed_right = np.random.uniform(low=0, high=0, size=(3,))
                random_speed_length = np.random.uniform(low=0, high=0, size=(3,))
            combine.append(random_distance)
            combine.append(random_speed_left)
            combine.append(random_speed_right)
            combine.append(random_speed_length)
            nested.append(combine)
    values.append(nested)
   

    for i in range(agents-1):
        nested = []
        for j in range(8):
            combine = []
            random_distance = np.random.uniform(low=min_distance, high=max_distance, size=(3,))
            random_distance.sort()
            random_speed_left = np.random.uniform(low=min_speed, high=max_speed, size=(3,))
            random_speed_right = np.random.uniform(low=min_speed, high=max_speed, size=(3,))
            random_speed_length = np.random.uniform(low=min_speed_length, high=max_speed_length, size=(3,))
            combine.append(random_distance)
            combine.append(random_speed_left)
            combine.append(random_speed_right)
            combine.append(random_speed_length)
            nested.append(combine)
        values.append(nested)


    print(values[1])
 

    #'''
    def movement(rob, values, distances,i):
        index = [0,1,2,3,4,5,6,7]
        rank = [sorted(distances).index(x) for x in distances]
        sorted_distance = [x for _, x in sorted(zip(rank,index))]
        for j in sorted_distance:
            if(distances[j]>0):
                if (distances[j]<values[i][j][0][0]):
                    rob, speed_left, speed_right, time_ = movement_a(rob, values,i,j)
                    return rob, speed_left, speed_right, time_
                elif (distances[j]<values[i][j][0][1]):
                    rob, speed_left, speed_right, time_ = movement_b(rob, values,i,j)
                    return rob, speed_left, speed_right, time_
                elif (distances[j]<values[i][j][0][2]):
                    rob, speed_left, speed_right, time_ = movement_c(rob, values,i,j)
                    return rob, speed_left, speed_right, time_

        rob, speed_left, speed_right, time_ = normal_movement(rob, values,i,j)
        return rob, speed_left, speed_right, time_

    def movement_a(rob, values,i,j):
        speed_left = values[i][j][1][0]
        speed_right = values[i][j][2][0]
        time_ = values[i][j][3][0]

        rob.move(speed_left, speed_right , time_)
        print('movement a ',speed_left, speed_right, time_ )
        return rob, speed_left, speed_right, time_

    def movement_b(rob, values,i,j):
        speed_left = values[i][j][1][1]
        speed_right = values[i][j][2][1]
        time_ = values[i][j][3][1]
        
        rob.move(speed_left, speed_right , time_)
        print('movement b ',speed_left, speed_right, time_ )
        return rob, speed_left, speed_right, time_

    def movement_c(rob, values,i,j):
        speed_left = values[i][j][1][2]
        speed_right = values[i][j][2][2]
        time_ = values[i][j][3][2]
        
        rob.move(speed_left, speed_right , time_)
        print('movement c ',speed_left, speed_right, time_ )
        return rob, speed_left, speed_right, time_

    def normal_movement(rob, values,i,j):
        rob.move(50,50,10)
        print('normal movement ', 50, 50, 10)
        return rob,50,50,10
    
    def bump_occured(distances):
        
        for j in distances:
            if(j>0.00001):
                if(j<0.04):
                    print("**BUMP**")
                    return 1
        return 0

    scores = []
    fitness = [None] * agents
    start_time = 2000  #increasing time with each loop?
    
    
    for i in range(agents):

          
        print('create rob')
        #signal.signal(signal.SIGINT, terminate_program)
        rob = robobo.SimulationRobobo().connect(address='192.168.178.81', port=19997)
        rob.play_simulation()

        
        
 
        time.sleep(2)
        #print(np.array(rob.read_irs()))
        print('start with agent',i)
        

        time_left = start_time
        speed_sum = 0
        bump_sum = 0
        left_vs_right = [] 
        while(time_left>=0):
            distances = np.array(rob.read_irs())
            rob, speed_left, speed_right, time_ = movement(rob, values, distances,i)
            speed_sum += ((speed_left+speed_right)/2*time_)
            for t in range(round(int(time_)/10)):
                distances = np.array(rob.read_irs())
                bump_sum += bump_occured(distances)
            left_vs_right.append(abs(speed_left-speed_right))
            print(abs(speed_left-speed_right))
            time_left -= time_
            print('time_left ', time_left)
        score = speed_sum/start_time - bump_sum *500 - statistics.mean(left_vs_right)*4
        print("score of agent ",i," :",score,"speed score:", speed_sum/start_time,"bump score", -bump_sum*500,"turn score", -statistics.mean(left_vs_right)*4)
        scores.append([i, score, speed_sum/start_time, -bump_sum*500, -statistics.mean(left_vs_right)*4])
        fitness[i] = score
        rob.pause_simulation
        rob.stop_world()
        print('sleep')
        rob.wait_for_stop()
        print('stopped?')
        rob.disconnect()
        print('disconnected')
    
    print(fitness)
        
        
        
    
if __name__ == "__main__":
    main()
