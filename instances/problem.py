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
        #   - for each patient, the admission date (negative values for optional patient for postponed scheduling period)
        #       I. for mandatory patients, admision date > 0 and release_date <= admission <= due_date
        #       II. for optional patients, release_date <= admission (the others became soft costraints --> penalize in obj func)
        #   - for each patient, the allocation of the room (-1 if the patient has not been accepted)
        #       I. room_id should not be in the list of incopatible_id
        #       II. be careful on capacity costraints on rooms
        #       III. people of different genders cannot be in the same room
        #   - for each nurse, a vector 1x(3*dayx), where the i-th element indicates in which room she is working (-1 if she is not working)
        #       I.  all costraints about assigning a nurse to a room are soft costraints --> penalize on the obj function
        #       II. we need to check that there are negative values on the shifts she is not working
        #       III. we need to check that each non-empty room has assigned a nurse
        #   - a matrix (num_patients) x 2 in which the i-th row contains the info about which OT the patient i is operated in and in which day 
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
        #   nella definizione dei vicini terremo conto di questa cosa, ma potrebbe essere utile se riscontriamo problemi)
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
        # first I check If all nurses have received a scheduling
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
        for day in range(self.days):
            id_day = day*3
            
            # if someone is in the room in a certain day, I check if exactly a nurse is assigned to the room
            for id_room, list in enumerate(state.patients_per_room[day]):
                if state.patients_per_room[day][id_room] != []: 
                    cont_earlysh = 0
                    cont_latesh = 0
                    cont_nightsh = 0
                    
                    for sched in state.nurses_shifts.values():
                            # early shift
                            id_shift = id_day + 0
                            try:
                                if id_room in sched[id_shift]: cont_earlysh+=1
                            except:
                                pass
                            
                            # late shift
                            id_shift = id_day + 1
                            try:
                                 if id_room in sched[id_shift]: cont_latesh+=1
                            except:
                                pass
                            
                            # night shift
                            id_shift = id_day + 2
                            try:
                                if id_room in sched[id_shift]: cont_nightsh+=1
                            except:
                                pass
                
                    # if only one of this cont is still 0  we have an unfeasible point
                    if cont_earlysh != 1 or cont_latesh != 1 or cont_nightsh != 1:
                        flag = False
        
        return flag
            

    def objective_function(self, state):
        # if a state is passed to this function we assume it is feasible
        value_obj = 0
        
        # penalizing age groups 
        for day, prospetto_giornaliero in enumerate(state.patients_per_room):
            for prospetto_room in prospetto_giornaliero:                
                # prospetto_room is a list containing the ids of the people in the room
                set_agegorups = set()
                for pers in prospetto_room:
                    set_agegorups.add(self.people[pers].age_group)

            # penalizing when there is more than 1 age group
            if len(set_agegorups) > 1: value_obj+= self.weights['room_mixed_age']
        
        
        
        # penalties for surgical delays + unscheduled patients
        for id_pat, value in state.dict_admission.items():
            if value[1] == -1: value_obj += self.weights['unscheduled_optional']
            elif self.patients[id_pat].mandatory:
                delay =  min([self.patients[id_pat].surgery_due_day - value[1],0])
                value_obj += delay*self.weights['patient_delay']
                
                
        # costs for openenig a OT + penalizing surgeon transfer
        for id_OT, prospetto_per_OT in state.scheduling_OTs.items():
            
            list_set_ot_per_surgeon = {}
            surgeon_ids = self.surgeons.keys()
            for id_surg in surgeon_ids:
                list_set_ot_per_surgeon[id_surg] = [set() for _ in range(self.days)]
            
            for day, prospetto_giornaliero in enumerate(prospetto_per_OT):
                set_OTs = set()
                # prospetto_giornaliero is a list containing all the ids of the patients who are operated in the OT in a certain day
                for id_pat in prospetto_giornaliero:
                    list_set_ot_per_surgeon[self.patients[id_pat].surgeon_id][day].add(id_OT)
                    set_OTs.add(id_OT)
                
                # dding cost for opened OTs
                value_obj += self.weights['open_operating_theater'] * len(set_OTs)
            
            # adding costs for surgeon transfers
            for elem in list_set_ot_per_surgeon.values():
                for insieme_OTS in elem:
                    value_obj += self.weights['surgeon_transfer']* min([0, len(insieme_OTS)-1])
                    
                    
        # costs of assigning a nurse with not enough skill level to a room + workload + continuity of care
        set_of_nurse_par_people = {}
        for id_peo in self.people.keys():
            set_of_nurse_par_people[id_peo] = set()
        
        for id_nurse, sched in state.nurses_shifts.items():
            for id_shift, room_vec in enumerate(sched):
                if room_vec != -1:
                    sum_workload = 0
                    for room in room_vec:
                        # id_shift = day*3 + {0;1;2} --> day = 1/3 * id_shift + 1/3*{0;1;2} in [1/3*id_shift; 1/3 *id_shift + 2/3]
                        id_pat_vec = state.patients_per_room[int(id_shift/3)][room]
                        for id_pat in id_pat_vec:
                            
                            set_of_nurse_par_people[id_peo].add(id_nurse)
                            
                            if id_pat in self.patients.keys():
                                # id_shift = data_accept*3 + x --> x = id_shift - data_accept*3
                                skill_min_required = self.patients[id_pat].skill_level_required[id_shift - state.dict_admission[id_pat][1]*3]
                                sum_workload += self.patients[id_pat].workload_produced[id_shift - state.dict_admission[id_pat][1]*3]
                            else:
                                skill_min_required = self.occupants[id_pat].skill_level_required[id_shift]
                                sum_workload += self.occupants[id_pat].workload_produced[id_shift]
                            
                                
                            value_obj += self.weights['room_nurse_skill'] * max(0, skill_min_required - self.nurses[id_nurse].skill_level)
                            
                    # end for on room_vec
                    # I have to dermine the max_load for a nurse by searching it in the dictionary
                    list_shift = self.nurses[id_nurse].working_shift
                    for elem in list_shift:
                        idx_x = 3*elem['day'] + elem['shift']
                        if idx_x == id_shift: max_workload = elem['max_load']
                        
                    value_obj += self.weights['nurse_eccessive_workload'] * max(0, sum_workload - max_workload)
                                
            
        for set_of_nurses in set_of_nurse_par_people:
            value_obj += len(set_of_nurses)
        
        return value_obj
            
            
            
        

    
    