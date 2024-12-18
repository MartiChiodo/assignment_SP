import numpy as np
from instances import *
from solvers import *
import json 

# impporting data from toy.json
with open("./data/toy.json") as input_f:
    data = json.load(input_f)


# Initializing the istances of the problem
hospital = Hospital(data['rooms'], data['operating_theaters'] ,data['days'])
nurses = [Nurse(elem) for elem in data['nurses']]
pat = [Patient(elem, hospital) for elem in data['patients']] 
patients = [elem.encoding_agegroup(data['age_groups']) for elem in pat]
occ = [Occupant(elem, hospital) for elem in data['occupants']]
occupants = [elem.encoding_agegroup(data['age_groups']) for elem in occ]
surgeons = [Surgeon(elem) for elem in data['surgeons']]


print(hospital.occupation)
p = Problem()


with open("./settings/solver_setting.json") as f:
    solver_setting = json.load(
        f
    )
ga = GRASP_Solver(solver_setting)
ga.solve(p)
