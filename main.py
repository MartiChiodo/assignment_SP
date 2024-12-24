import numpy as np
from instances import *
from solvers import *
import json 

# impporting data from toy.json
with open("./data/toy.json") as input_f:
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

print(hospital.occupation)
p = Problem(surgeons, nurses, patients, occupants, hospital, weights, data['days'])

dict_admission_0 = {'p0' : ['t0', 4, 0], 'p1': ['t0', 6, 1]}
initial_state = State(dict_admission_0, [])

print(p.verifying_costraints(initial_state))



