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
        #   III. nurses_shifts --> for each shift, we store in which room a nurse works (each col is a shift, each row is a nurse) (-1 if nurse is not working in that shift)
        
        
    def add_state(self, state):
        self.state = state
        
    
        
    def verifying_costraints(self, state):
        
        flag = True  # true if state is feasible
        
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
            
        
        return flag
            

            
            
            
        

    
    