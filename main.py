import numpy as np
from instances import *
from solvers import *
import json 

# impporting data from toy.json
with open("./data/ihtc2024_test_dataset/test03.json") as input_f:
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

dict_admission_0 = {'p0' : ['t0', 4, 0], 'p1': ['t0', 6, 1]}


# ciao Sophie qui ti faccio un piccolo spiegone del casotto che ho fatto.
# La nostra matrice per salvarci le assegnazioni stanza - nurse è molto comoda per verificare i vincoli
# ma un po' meno comoda da creare, perciò ho creato un po' di funzioni che ci facilitino il lavoro.
# Nella classe nurse ho aggiunto un valore al dizionario 'working_shift' che ci permette di assegnare le stanze al turno dell'infermiera.
# Per rendere la cosa più easy ho aggiunto anche una funzione che data una lista di stanze va a riempire opportunamente questo nuovo valore.
# La matriciona comoda verrà poi calcolata mentre si crea la istanza dello Stato con una funzione apposita. Qui di seguito ti faccio vdere i passaggi chiave     

# proviamo a generare uno stato casuale con la nuova funzione
rnd_state = p.generating_feasible_state()
print(rnd_state.dict_admission)


print(p.verifying_costraints(rnd_state))

# per ora la configurazione non va bene perché c'è qualche stanza scoperta ma ho sonno

print(p.objective_function(rnd_state))



