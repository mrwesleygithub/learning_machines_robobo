#!/usr/bin/env python3
from __future__ import print_function
from ipaddress import ip_address

import time
from typing import MutableMapping
import numpy as np
import robobo
import cv2
import sys
import signal
import random
import prey
import statistics
import pickle



def terminate_program(signal_number, frame):
    print("Ctrl-C received, terminating program")
    sys.exit(1)





#evolutionary specifics:
#Basically, there are three different behaviours of the robot, or 3 choices. Intuitively, this might result in 3
#different settings, a small turn, a medium turn and a large turn, depending on the input of the sensors.
#For each sensor (8 in total), we have 3 different distance values, if one of these distance values is exceeded
#we let the robot change the speed of the wheels to the corresponding speed_left, speed_right variables for a length
#of speed_length. Thus, in total, for each agent we have 8*3*4 = sensors*choices*robot_variables variables stored. 
#All information about the robot (behaviour) is stored in the variable values. The values that are stored here are the following:
#values[x] contains all information about agent number x
#values[x][y] at y we can choose between one of the 8 sensors, each sensor has specific attributes and behaviour
#values[x][y][z] at z we select variable 1...4, refering to the distance, left wheel speed, right wheel speed and speed duration
#values[x][y][z][c] at c we select one of the three choices.

#The fitness is determined by the average speed of the robot (speed measured as the net forward or backward movement) discounted
#for bumps (that is having the closest proximity of one of the sensors falling below a certain treshold: 0.03) - the difference
#between the two wheels, thus discounting for making turns. 


def main():

    #these are the bounds for the variables. We want to limit the search space, and meet requirements
    #e.g., we can not have a negative speed_length, and a distance under 0 also does not make sense. 
    min_speed = -100
    max_speed = 100
    min_distance = 0
    max_distance = 0.3
    min_speed_length = 5
    max_speed_length = 500
    agents = 60 
    values = []
    scores = []
    start_time = 4000  #increasing time with each loop?
    parents_needed = 20
    children_per_parent = 1
    single_parent_chance = 0.15
    sd = 10
    gene_mutation_chance = 0.5
    mutation_chance = 0.85
    runs = 100
    population = agents+parents_needed/2*children_per_parent
    number_of_agents_to_run = agents
    tournament_entries = 5
    continue_with_run = True
    file_name = "values_run_48+7"
    ip_address = "192.168.2.12"   #'192.168.178.80' home, vu 145.108.71.5, seb 192.168.2.12
  

    # We add one robot with pre-defined variables, just to compare performance, later we might want to kick-start
    # the evolutionary proces by adding good-working robots here. the others are generated randomly in the section below
    #and the proces is explained in more detail.
    if continue_with_run:
        with open(file_name, "rb") as fp:   # Unpickling
            values = pickle.load(fp)


    else:
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
                #This refers to the distance that a sensor can register before triggering a reaction, they are sorted
                #such that we have initial ordered behaviour. (e.g. we want the short sensor distance to generate a larger
                # turn than the large sensor distance eventually)
                random_distance = np.random.uniform(low=min_distance, high=max_distance, size=(3,))
                random_distance.sort()
                #the corresponding left/right _wheel speed are created when distance is triggered, again 3 values since 3 options.
                random_speed_left = np.random.uniform(low=min_speed, high=max_speed, size=(3,))
                random_speed_right = np.random.uniform(low=min_speed, high=max_speed, size=(3,))
                #the length/time of the turn. 
                random_speed_length = np.random.uniform(low=min_speed_length, high=max_speed_length, size=(3,))
                combine.append(random_distance)
                combine.append(random_speed_left)
                combine.append(random_speed_right)
                combine.append(random_speed_length)
                nested.append(combine)
            #all values are stored here as lists, see the part above that shows an example as to how to reference and retract them
            values.append(nested)


    #print(values[1])
 

    #'''
    #sorts the distances of the sensors and uses the sensor that is closest to the edge to guide decisions.
    #if the distance to this sensor is less than one of the three distance values of the agent, a movement is triggered
    #movement a b or c, which are ordered. 
    #! something should be created to make double connections possible, e.g. to avoid going from left to right to left to right when stuck
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

    #When triggered, the speed for both wheels and the duration of the movement are retrieved from the values of the agent.
    def movement_a(rob, values,i,j):
        speed_left = values[i][j][1][0]
        speed_right = values[i][j][2][0]
        time_ = values[i][j][3][0]

        rob.move(speed_left, speed_right , time_)
        #print('movement a ',speed_left, speed_right, time_ )
        return rob, speed_left, speed_right, time_

    def movement_b(rob, values,i,j):
        speed_left = values[i][j][1][1]
        speed_right = values[i][j][2][1]
        time_ = values[i][j][3][1]
        
        rob.move(speed_left, speed_right , time_)
        #print('movement b ',speed_left, speed_right, time_ )
        return rob, speed_left, speed_right, time_

    def movement_c(rob, values,i,j):
        speed_left = values[i][j][1][2]
        speed_right = values[i][j][2][2]
        time_ = values[i][j][3][2]
        
        rob.move(speed_left, speed_right , time_)
        #print('movement c ',speed_left, speed_right, time_ )
        return rob, speed_left, speed_right, time_

    #When no response is triggered, the car just goes straight ahead.
    #! in a later stage, this can also be made evolutionary
    def normal_movement(rob, values,i,j):
        rob.move(50,50,10)
        #print('normal movement ', 50, 50, 10)
        return rob,50,50,10
    
    #returns 1 when there is is a (possible) collission with an object (when an ir sensor registers a nonzero value which is <0.04)
    def bump_occured(distances):
        
        for j in distances:
            if(j>0.00001):
                if(j<0.04):
                    #print("**BUMP**")
                    return 1
        return 0

    
# tournament selection
    def parent_selection(values, scores, k, agents, parents_needed):
        #tournament selection
        selected = []
        for f in range(parents_needed):
            agents_selected = list(np.random.randint(low = 0,high=agents,size=k))
            #print("agent selected for parent selection tournament",agents_selected)
            fitness = []
            for q in agents_selected:
                fitness.append(scores[q])
            
            rank = [sorted(fitness).index(x) for x in fitness]
            #print("rank", rank)
            winner = [x for _, x in sorted(zip(rank,agents_selected))]
            #print("winner", winner)
            #print("fitness",fitness)
            selected.append(winner[len(winner)-1])
        print("parents selected for parent selection", selected)

        #retrieve parent dna 
        parent_dna = []   
        for i in selected:
            #print(i)
            parent_dna.append(values[i])
        return parent_dna
    
    #creation of offspring
    def offspring_creation(parent_dna, parents_needed, children_per_parent, single_parent_chance):
    
        order = random.sample(range(parents_needed), parents_needed)
        parent = 0
        child_count = 0
        offspring = []
        
        for i in range(0,int(parents_needed/2)):
            parent1 = parent_dna[order[parent]]
            parent+=1

            parent2 = parent_dna[order[parent]]
            parent+=1

            for x in range(0,children_per_parent):
                child = parent_dna[1]
                if random.random()<single_parent_chance:
                    if random.random()<0.5:
                        offspring.append(parent1)
                    else:
                        offspring.append(parent2)
                    child_count+=1

                #values[x][y] at y we can choose between one of the 8 sensors, each sensor has specific attributes and behaviour
                #values[x][y][z] at z we select variable 1...4, refering to the distance, left wheel speed, right wheel speed and speed duration
                #values[x][y][z][c] at c we select one of the three choices.
                
                #just adding a parent to create the reference in the offspring, we will adjust values later
                offspring.append(parent1)
                #looping through values and taking the value of parent 1 or 2 with some probability, or
                # take the average +- a deviation of the parents
                for c in range(8):
                    for d in range(4):
                        for e in range(3):
                            #select average (if) or one of the two parents' values (else)
                            if random.random()<0.5:
                                #adding average of both parents
                                offspring[child_count][c][d][e] = (values[parent-2][c][d][e] + values[parent-1][c][d][e])/2 

                            else:
                                #select value of parent 1 (if) or the value of parent 2 (else) + deviation
                                if random.random()<0.5:
                                    offspring[child_count][c][d][e] = values[parent-2][c][d][e]
                                else:
                                    offspring[child_count][c][d][e] = values[parent-1][c][d][e]


                child_count+=1

        return offspring, child_count
    
    #mutates the offspring
    def offspring_mutation(offspring, mutation_chance, gene_mutation_chance, sd, child_count):
        for child in range(0,child_count):
            if random.random()<mutation_chance:
                 for c in range(8):
                    for d in range(4):
                        for e in range(3):
                            if random.random()<gene_mutation_chance:
                                offspring[child][c][d][e] = mutation_limit(offspring[child][c][d][e] * (1+ np.random.normal(0,sd)/100), d )
                               
        return offspring

    #if mutation exceeds the limits, the limit value is used. 
    def mutation_limit(x,d):
        if(d==1):
            if(x<min_distance):
                return min_distance
            elif(x>max_distance):
                return max_distance
            else:
                return x
        elif(d==4):
            if(x<min_speed_length):
                return min_speed_length
            elif(x>max_speed_length):
                return max_speed_length
            else:
                return x
        else:
            if(x<min_speed):
                return min_speed
            elif(x>max_speed):
                return max_speed
            else: return x
    
    #after running the robot, this part determines its score/fitness/
    def evaluate_robot(rob, values, i):
        time_left = start_time
        speed_sum = 0
        bump_sum = 0
        left_vs_right = [] 

        #let the robot run, untill its time is up (to make comparison fair. After each movement, it is checked if time is left
        #and a new action (movement) is retrieved. 
        while(time_left>=0):
            distances = np.array(rob.read_irs())
            rob, speed_left, speed_right, time_ = movement(rob, values, distances,i)
            speed_sum += ((speed_left+speed_right)/2*time_)
            for t in range(round(int(time_)/10)):
                distances = np.array(rob.read_irs())
                bump_sum += bump_occured(distances)
            left_vs_right.append(abs(speed_left-speed_right))
            #print(abs(speed_left-speed_right))
            time_left -= time_
            #print('time_left ', time_left)
        
        #the fitness function of the robot, gaining for average speed, but losing for collisions and needing steering connections.
        score = speed_sum/start_time - bump_sum *50 - statistics.mean(left_vs_right)
        print("score of agent ",i," :",score,"speed score:", speed_sum/start_time,"bump score", -bump_sum*500,"turn score", -statistics.mean(left_vs_right))
        return score, speed_sum/start_time, -bump_sum*500, -statistics.mean(left_vs_right) 
    
    #selection of the parents
    def selection(values, offspring, scores, agents, population_size):
        #pure elitism
        chosen = [] 
        negative_score = np.negative(scores)
        order =  [sorted(negative_score).index(x) for x in negative_score]
        values_selection = []
        scores_selection = []

        
        for c in range(len(scores)):
            if order[c]<agents:
                chosen.append(c)
        
        print("scores",scores)
        print("chosen", chosen)
        for t in chosen:
            if(t < agents):
                values_selection.append(values[t])
                scores_selection.append(scores[t])
            else:
                values_selection.append(offspring[t-agents])
                scores_selection.append(scores[t])

        return values_selection, scores_selection

    #disconnecting the robot
    def disconnect_robot(rob):
        rob.pause_simulation
        rob.stop_world()
        print()
        print('robot sleeps')
        rob.wait_for_stop()
        print('robot stopped')
        rob.disconnect()
        print('robot disconnected')
        print()
        return rob

            
            
        population = population[chosen]    
        population_fitness = scores[chosen]

        return values, scores

    #start evolutionary process, by checking the parents:
    
    
    #running the ev
    for run in range(0,runs):
        if run > 30:
            tournament_entries = 3
        print("---------------------------------------------------")
        print("Run:",run)
        for i in range(number_of_agents_to_run):

            #create the connection to the robot
            #print('create rob')
            #signal.signal(signal.SIGINT, terminate_program)
            rob = robobo.SimulationRobobo().connect(address=ip_address, port=19997)
            rob.play_simulation()

            
            time.sleep(2.5)
            print("Run", run, 'start with agent',i)
            if run>0:
                print("global high score so far:", np.max(scores))
            

            #EVEN DENKEN AAN HOE IK DIE LOOP MET AGENTS GA OPLOSSEN, DE ERROR KOMT VANWEGE DE I
            if (run == 0):
                score, speed_score, bump_score, turn_score = evaluate_robot(rob, values, i)
            else:
                score, speed_score, bump_score, turn_score = evaluate_robot(rob,offspring_dna_mutated,i)
            #scores.append([i, score, speed_score, bump_score, turn_score])
            scores.append(score)
            #fitness[i] = score
            
            #stopping the simulation, thus resetting the environment for the next agent.
            rob = disconnect_robot(rob)
            
        
        if (run>0):
            values, scores = selection(values, offspring_dna_mutated, scores, agents, population)

        parent_dna = parent_selection(values,scores, tournament_entries, agents, parents_needed)
        offspring_dna, child_count =  offspring_creation(parent_dna, parents_needed, children_per_parent, single_parent_chance)
        offspring_dna_mutated = offspring_mutation(offspring_dna, mutation_chance, gene_mutation_chance, sd, child_count)

        
        best_score = np.max(scores)
        best_score_index_number = scores.index(best_score)
        print()
        print('The best fitness score is now:', best_score)
        print('This score is obtained by robot dna with index number: ', best_score_index_number)

        print('The behaviour of this robot is shown one more time:')
        rob = robobo.SimulationRobobo().connect(address=ip_address, port=19997)
        rob.play_simulation()
        time.sleep(2)
        score, speed_score, bump_score, turn_score  = evaluate_robot(rob,values,best_score_index_number)
        rob = disconnect_robot(rob)
        print("This robot now produced a score of:", score)

        print('The mean scores of the robots is now:', np.mean(scores), statistics.mean(scores))
        print('The std of the robot scores is now:', np.std(scores))
        print("these are the scores", scores)
        print()

        number_of_agents_to_run = child_count

        with open("values_run_48+"+str(run), "wb") as fp:   #Pickling
            pickle.dump(values, fp)
        
        with open("scores_run_48+"+str(run), "wb") as fp:   #Pickling
            pickle.dump(scores, fp)
 

        # with open("test", "rb") as fp:   # Unpickling
        #b = pickle.load(fp)

        
        
    
if __name__ == "__main__":
    main()
