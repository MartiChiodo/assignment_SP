
import numpy as np
from instances import *
from solvers import GRASP_Solver
import random
import os
from timeit import default_timer as timer


def main():
    
    import json
    import sys
    
    file_path = os.path.join(sys.path[0], "data", "ihtc2024_test_dataset", "test05.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path) as input_f:
        data = json.load(input_f)


    # Initializing the istances of the problem
    hospital = Hospital(data['rooms'], data['operating_theaters'] ,data['days'])
    nurses = {elem['id']: Nurse(elem) for elem in data['nurses']}
    pat = {elem['id']: Patient(elem, hospital) for elem in data['patients']}
    patients = { key: elem.encoding_agegroup(data['age_groups']) for key,elem in pat.items()}
    occ = {elem['id']: Occupant(elem, hospital) for elem in data['occupants']}
    occupants = { key: elem.encoding_agegroup(data['age_groups']) for key,elem in occ.items()}
    surgeons = {elem['id']: Surgeon(elem) for elem in data['surgeons']}
    weights = data['weights']

    p = Problem(surgeons, nurses, patients, occupants, hospital, weights, data['days'])
    

    # the initial guess is generated randomly with a function
    random.seed(min(343310, 339268))
    rnd_state = p.generating_feasible_state()
    
    # SOLVING THE OPT PROBLEM
    print('\n')
    print('*********************************')
    print('SOLVING THE OPTIMIZATION PROBLEM')
    solver = GRASP_Solver(p, rnd_state)
    start_timer = timer()
    best_solution, best_f, plot = solver.solve(num_restart=2)
    end_timer = timer()

    print('Best obj function = ', best_f)
    print('Elapsed time = ', end_timer-start_timer, ' sec')

    p.objective_function(best_solution, opt=1)
    plot.show()
    
    # Data to be written
    dictionary = {}

    lista_pat = []
    for id_pat in patients.keys():
        dict_admission_pat = best_solution.dict_admission[id_pat]
        room = 'r'+ str(dict_admission_pat[2])
        
        if dict_admission_pat[1] == -1: 
            dict_admission_pat[1] = 'none'
            
            dic_prv = {
                    "id": id_pat,
                    "admission_day": dict_admission_pat[1],
                }  
            
        else:
            dic_prv = {
                        "id": id_pat,
                        "admission_day": dict_admission_pat[1],
                        "room": room,
                        "operating_theater": dict_admission_pat[0]
                    }  
        
        lista_pat.append(dic_prv)

    dictionary['patients'] = lista_pat   

    lista_nurses = []
    for id_n, id_nurses in enumerate(nurses.keys()):
        dic_prv = {'id': id_nurses}
        lista_assignments = []
        
        for id_s, sched in enumerate(nurses[id_nurses].working_shift):
            rooms = best_solution.room_to_be_assigned[id_n][id_s]
            rooms_right_syntax = ['r'+ str(elem) for elem in rooms ]
            
            if sched['shift'] == 0: shift = 'early'
            elif sched['shift'] == 1: shift = 'late'
            elif sched['shift'] == 2: shift = 'night'
            
            dict_ass = {
                'day': sched['day'],
                'shift': shift,
                'rooms': rooms_right_syntax
            }
            
            lista_assignments.append(dict_ass)
        
        dic_prv['assignments'] = lista_assignments
            
        lista_nurses.append(dic_prv)

    dictionary['nurses'] = lista_nurses


    # Serializing json
    json_object = json.dumps(dictionary, indent=4)
    
    # Writing to sample.json
    file_path = os.path.join(sys.path[0], "results", "output_file.json")
    with open(file_path, "w") as outfile:
        outfile.write(json_object)


if __name__ == '__main__':
    
    main()