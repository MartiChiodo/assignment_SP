import math
import numpy as np


class Problem():
    
    def __init__(self, surgeons, nurses, patients, occupants, hospital, weights, days):
        self.surgeons = surgeons
        self.nurses = nurses
        self.patients = patients
        self.occupants = occupants
        self.people = patients |occupants
        self.hospital = hospital
        self.state = []
        self.weights = weights
        self.days = days
        
        # DECISIONAL VARIABLES and COSTRAINTS
        #   - for each patients, the admission date (negative values for optional patient for postponed scheduling period)
        #       I. for mandatory patients, admision date > 0 and release_date <= admission <= due_date
        #       II. for optional patients, release_date <= admission (the others became soft costraints --> penalize in obj func)
        #   - for each patients, the allocation of the room (-1 patient has not been accepted)
        #       I. room_id should not be in the list of incopatible_id
        #       II. be careful on capacity costraints on rooms
        #       III. people of different genders cannot be in the same room
        #   - for each nurse, a vector 1x(3*dayx), where the i-th element indicates in which room she is working (-1 if she is not working)
        #       I.  all costraints about assigning a nurse to a room are soft costraints --> penalize on the obj function
        #       II. we need to check that there are negative values on the shifts she is not working
        #       III. we need to check that each non-empty room has assigned a nurse
        #   - a matrix (num_patients) x 2 in which the i-th row contains the info about in which OT the patient i is operated and in which day 
        #       I. verifying that the capacities about OTs and surgeons are satisfied
        
        # HOW WE STORE THE DECISION VARIABLES
        #   I. dict_admission -->  dictionary such that id_patient : [ot_id, surgery_date, room]
        #   II. nurses_shifts --> for each shift, we store in which room a nurse works (each col is a shift, each row is a nurse) (-1 if nurse is not working in that shift)
        #       This structure is stored as a dictionary: key = nurse, value = array (3*days)x1 with the indication of in which rooms she is working (potenzialmente è un dizionario a di liste di liste
        #         E.g: n0: [-1, [r0 r1], [r1], ... ],  n1 = [-1, -1, -1, ...], ...)
        
    
        
    def verifying_costraints(self, state):
        
        flag = True  # true if state is feasible
              
        # CHECKING IF STATE IS AMMISSIBLE
        # faccio un controllo sull'esistenza delle sale operatorie e delle stanze assegnate (non dovrebbe essere necessario perché si parte da una configurazione ammissibile e 
        #   nella definizione dei vicini terremo cono di questa cosa, ma potrebbe essere utile se riscontriamo problemi)
        for key, value in state.dict_admission.items():
            if len(value) != 3:
                raise ValueError('STATO NON AMMISSIBILE: la riga del pazione {key} ha una lunghezza diversa da 3.'.format(key=repr(key)))

            id_OT = value[0]
            id_ROOM = value[2]
            
            if id_OT not in self.hospital.avalaibilityOT.keys():
                raise ValueError('STATO NON AMMISSIBILE: la sala operatoria {id_OT} non esiste.'.format(id_OT=repr(id_OT)))

            if id_ROOM not in range(self.hospital.n_rooms):
                raise ValueError('STATO NON AMMISSIBILE: la stanza post-ricovero numero {id_ROOM} non esiste.'.format(id_ROOM=repr(id_ROOM)))
            
            
        # AMMISIBILITY OF STATE BASED ON NURSES' SCHEDULING
        # first I check If alla nurses have received a scheduling
        len_state = len(state.nurses_shifts.keys())
        len_expected = len(self.nurses.keys()) 
        if len_state != len_expected :
            raise ValueError('STATO NON AMMISSIBILE: nurses_shifts dovrebbe avere lunghezza {len_expected} ma ha lunghezza {len_state}.'.format(len_expected = repr(len_expected), len_state = repr(len_state)))
        
        # checking if all the nurses exist
        for id_nurse in state.nurses_shifts.keys():
            if id_nurse not in self.nurses.keys():
                raise ValueError('STATO NON AMMISSIBILE: La nurse con id {id} non esiste.'.format(id=repr(id_nurse)))
        
        # for each week I check if the nurse should be working in the shift she has been assigned
        for id_nurse, schedule in state.nurses_shifts.items():
            # each element represents the whole scheduling of a single nurse --> schedule is a list of 3*days elements where -1 means she is not working.
            # If she is working schedule contains a list of the rooms she has been assigned
            
            # first I create a binary array indicating whether the nurse should be working
            should_work  = [False for _ in range(self.days * 3)]
            nurse_priorscheduling = self.nurses[id_nurse].working_shift

            for shift in nurse_priorscheduling:
                id = shift['day'] *3 + shift['shift']          
                should_work[id] = True
                
        
            for id, rooms in enumerate(schedule):
                # check if the nurse is working according to the apriori scheduling
                if should_work[id] and rooms == -1:
                    # case in which nurse should be working but she is not assigned to any room
                    raise ValueError('STATO NON AMMISSIBILE: la nurse {id_nurse} dovrebbe lavorare nel turno {id}.'.format(id_nurse=repr(id_nurse), id=repr(id)))
                elif not should_work[id] and rooms != -1:
                    # case in which nurse should not be working but she is assigned to a room
                    raise ValueError('STATO NON AMMISSIBILE: la nurse {id_nurse} non dovrebbe lavorare nel turno {id}.'.format(id_nurse=repr(id_nurse), id=repr(id)))
               
                # check if the nurse is assigned to an existing room
                if rooms != -1:
                    for room in rooms:
                        if should_work[id] and room not in range(self.hospital.n_rooms):
                            raise ValueError('STATO NON AMMISSIBILE: Nurse assegnata alla stanza inesistente {room}.'.format(room=repr(room)))
                   
            
        
        # creating the useful matrix we wil largely use
        state.adding_matrix(self.hospital.creating_matrix_dayxroomxpatients(state.dict_admission, self))

        
        # COSTRAINTS ON ROOM
        # no gender mix + compatible rooms
        for day in range(len(state.patients_per_room)):
            for room in range(len(state.patients_per_room[day])):
                lista_genderinaroom = []
                if len(state.patients_per_room[day][room]) >=1:
                    for id_pat in state.patients_per_room[day][room]:
                        patient = self.people[id_pat]
                        lista_genderinaroom.append(patient.gender)
                        
                        try:
                            flag = room not in patient.incompatible_room_ids #check whether patient is in an incompatible room
                        except:
                            pass
                            
                            
                    flag = len(set(lista_genderinaroom)) <= 1 # checking that in a room there are people of same gender
                
                # cheking the costraints on capacities per room
                flag = len(state.patients_per_room[day][room]) <= self.hospital.capacity_per_room[room]
        
        
        # COSTRAINTS ON SURGICAL PLANNING
        dict_surgerytimepersurgeon = {key : elem.max_surgery_time  for key,elem in self.surgeons.items()}
        dict_surgerytimeperot =  self.hospital.avalaibilityOT
        for id_patient,list in state.dict_admission.items():
            # checking if admission date is feasible    
            if self.people[id_patient].mandatory:
                flag = list[1] <= self.people[id_patient].surgery_due_day
                flag = list[1] >=  self.people[id_patient].surgery_release_day
            else:
                # for non mandatory we need to check that acceptance date is not further the last day
                flag = list[1] <= self.hospital.days
                flag = (list[1] >=  self.people[id_patient].surgery_release_day) or  list[1] == -1
                
            # subctracting surgery time from dictionary
            id_tempo = (list[1]-1) % 7 # % mod operator
            id_surg = self.people[id_patient].surgeon_id
            
            dict_surgerytimepersurgeon[id_surg][id_tempo] -= self.people[id_patient].surgery_duration
            flag = dict_surgerytimepersurgeon[id_surg][id_tempo] >= 0 # checkong that the time is still non-negative
            dict_surgerytimeperot[list[0]][id_tempo] -= self.people[id_patient].surgery_duration
            flag =  dict_surgerytimeperot[list[0]][id_tempo] >= 0 # checkong that the time is still non-negative
            
        
        # CHECKING IF ALL OCCUPIED ROOM HAS AT LEAST ONE NURSE ASSIGNED
        
             

        
        return flag
            

            
            
            
        

    
    