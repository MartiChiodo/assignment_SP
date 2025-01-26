import math
import numpy as np
import random
from .state import State
import copy


class Problem():
    
    def __init__(self, surgeons, nurses, patients, occupants, hospital, weights, days):
        # this class will contain all the information we have about the optimization pb
        self.surgeons = surgeons
        self.nurses = nurses
        self.patients = patients
        self.occupants = occupants
        self.people = patients |occupants
        self.hospital = hospital
        self.state = []
        self.weights = weights
        self.days = days


    # HOW WE STORE THE DECISION VARIABLES?
    # I. dict_admission --> dictionary such that id_patient : [ot_id, surgery_date, room],
    # from this data structure we are going to define the matrix dayxroomxpatient in which we store the scheduling of the rooms
    # II. nurses_shift --> This structure is stored as a dictionary: key = nurse, value = array (3*days)x1 with the indication of in which rooms she is working 
    #         E.g: {n0: [-1, [r0 r1], [r1], ... ],  n1 = [-1, -1, -1, ...], ...}
        
    def verifying_costraints(self, state):
        
        flag_feasible_state = True  # true if state is feasible
              
        # CHECKING IF STATE IS AMMISSIBLE BASED ON EXISTENCE OF OTs and ROOMS 
        for key, value in state.dict_admission.items():
            if len(value) != 3:
                raise ValueError('STATO NON AMMISSIBILE: la riga del pazione {key} ha una lunghezza diversa da 3.'.format(key=repr(key)))

            id_OT = value[0]
            id_ROOM = value[2]
            
            if id_OT not in self.hospital.capacity_per_OT.keys():
                raise ValueError('STATO NON AMMISSIBILE: la sala operatoria {id_OT} non esiste.'.format(id_OT=repr(id_OT)))

            if id_ROOM not in range(self.hospital.n_rooms) and not id_ROOM == None:
                raise ValueError('STATO NON AMMISSIBILE: la stanza post-ricovero numero {id_ROOM} non esiste.'.format(id_ROOM=repr(id_ROOM)))
            
            
            if not ((value[1]  >= 0 and value[1] <= self.days-1) or value[1] == -1) :
                raise ValueError('STATO NON AMMISSIBILE: la data di ammissione {data} non è valida'.format(data=repr(value[1])))
            
            
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

        ## CHECKING THE HARD COSTRAINTS OF THE OPTIMIZATION PROBLEM
        
        # COSTRAINTS ON ROOMS
        # State is not feasible if in some rooms there are patients of different gender + if a patient is assigned to an incompatible room
        for day in range(len(state.patients_per_room)):
            for room in range(len(state.patients_per_room[day])):
                lista_genderinaroom = []
                if len(state.patients_per_room[day][room]) >=1:
                    for id_pat in state.patients_per_room[day][room]:
                        patient = self.people[id_pat]
                        lista_genderinaroom.append(patient.gender)

                        try:
                            if room in patient.incompatible_room_ids:
                                flag_feasible_state = False
                                return False
                        except:
                            pass
                            
                            
                    if len(set(lista_genderinaroom)) > 1:
                        flag_feasible_state = False
                        return False
                
                # state is not feasibile if the number of people assigned to a room exceeds the capacity of the room
                if len(state.patients_per_room[day][room]) > self.hospital.capacity_per_room[room]:
                    flag_feasible_state = False
                    return False
         
        
        # COSTRAINTS ON SURGICAL PLANNING + COSTRAINTS ON ACCEPTANCE DATE
        dict_surgerytimepersurgeon = {key : copy.deepcopy(elem.max_surgery_time)  for key,elem in self.surgeons.items()}
        dict_surgerytimeperot =  copy.deepcopy(self.hospital.capacity_per_OT)
        for id_patient,list in state.dict_admission.items():
            # list = [id_OT, acceptance_date, room_id]
            if self.people[id_patient].mandatory:
                # for mandatory patients the surgery date should be in [release_date, due_date]
                flag_feasible_state = list[1] <= self.people[id_patient].surgery_due_day
                flag_feasible_state = list[1] >=  self.people[id_patient].surgery_release_day
            else:
                # for non mandatory we need to check that acceptance date is not further the last day or equal to -1
                flag_feasible_state = list[1] <= self.hospital.days
                flag_feasible_state = (list[1] >=  self.people[id_patient].surgery_release_day) or  list[1] == -1
                
            # subctracting surgery time from the dictionaries and checking if the components are still equal to/greater that 0
            id_tempo = list[1] 
            if not id_tempo == -1:
                id_surg = self.people[id_patient].surgeon_id
                
                new_time = dict_surgerytimepersurgeon[id_surg][id_tempo] - self.people[id_patient].surgery_duration
                dict_surgerytimepersurgeon[id_surg][id_tempo] = new_time
                
                if new_time < 0: 
                    flag_feasible_state = False
                    return False 
                
                new_time = dict_surgerytimeperot[list[0]][id_tempo] - self.people[id_patient].surgery_duration
                dict_surgerytimeperot[list[0]][id_tempo] = new_time
                if new_time < 0: 
                    flag_feasible_state = False
                    return False 
            
        
        # CHECKING IF ALL OCCUPIED ROOM HAS EXACTLY ONE NURSE ASSIGNED
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
                
                    # if only one of this counter is still 0  we have an unfeasible state
                    if cont_earlysh != 1 or cont_latesh != 1 or cont_nightsh != 1:
                        flag_feasible_state = False
        
        return flag_feasible_state
            

    def objective_function(self, state, opt = 0):
        # if a state is passed to this function we assume it is feasible
        weights_to_add = {elem: 0 for elem in self.weights.keys()}
        
        # penalizing age groups 
        for day, daily_scheduling in enumerate(state.patients_per_room):
            for room_scheduling in daily_scheduling:                
                # room_scheduling is a list containing the ids of the people in the room
                set_agegorups = set()
                for pers in room_scheduling:
                    set_agegorups.add(self.people[pers].age_group)

                # penalizing the differences between age groups
                if len(set_agegorups) > 0:
                    weights_to_add['room_mixed_age'] += max(set_agegorups) - min(set_agegorups) 
        
        
        
        # penalties for surgical delays + unscheduled patients
        for id_pat, value in state.dict_admission.items():
            if value[1] == -1: weights_to_add['unscheduled_optional'] += 1
            elif self.patients[id_pat].mandatory:
                delay = value[1] - (self.patients[id_pat].surgery_release_day-1) 
                weights_to_add['patient_delay'] += max(delay,0)
                
                
        # costs for openenig a OT + penalizing surgeon transfer
        list_set_ot_per_surgeon = {}
        surgeon_ids = self.surgeons.keys()
        for id_surg in surgeon_ids:
            list_set_ot_per_surgeon[id_surg] = [set() for _ in range(self.days)]
                
        for id_OT, prospetto_per_OT in state.scheduling_OTs.items():
            for day, prospetto_giornaliero in enumerate(prospetto_per_OT):
                set_OTs = set()
                # prospetto_giornaliero is a list containing all the ids of the patients who are operated in the OT in a certain day
                for id_pat in prospetto_giornaliero:
                    list_set_ot_per_surgeon[self.patients[id_pat].surgeon_id][day].add(id_OT)
                    set_OTs.add(id_OT)
                
                # adding cost for opened OTs
                weights_to_add['open_operating_theater'] +=  len(set_OTs)
            
        # adding costs for surgeon transfers
        for elem in list_set_ot_per_surgeon.values():
            for insieme_OTS in elem:
                weights_to_add['surgeon_transfer'] += max(len(insieme_OTS) - 1,0)
                
                    
        # costs of assigning a nurse with not enough skill level to a room + costs for excessive workload + penalizing if there is no continuity of care
        set_of_nurse_par_people = {}
        for id_pat in self.people.keys():
            set_of_nurse_par_people[id_pat] = set()
        
        for id_nurse, sched in state.nurses_shifts.items():
            for id_shift, room_vec in enumerate(sched):
                if room_vec != -1:
                    sum_workload = 0
                    for room in room_vec:
                        # id_shift = day*3 + {0;1;2} --> day = 1/3 * id_shift + 1/3*{0;1;2} in [1/3*id_shift; 1/3 *id_shift + 2/3]
                        id_pat_vec = state.patients_per_room[int(id_shift/3)][room]
                        for id_pat in id_pat_vec:
                            
                            set_of_nurse_par_people[id_pat].add(id_nurse)
                            
                            if id_pat in self.patients.keys():
                                # id_shift = data_accept*3 + x --> x = id_shift - data_accept*3
                                skill_min_required = self.patients[id_pat].skill_level_required[id_shift - state.dict_admission[id_pat][1]*3]
                                sum_workload += self.patients[id_pat].workload_produced[id_shift - state.dict_admission[id_pat][1]*3]
                            else:
                                skill_min_required = self.occupants[id_pat].skill_level_required[id_shift]
                                sum_workload += self.occupants[id_pat].workload_produced[id_shift]
                            
                                
                            weights_to_add['room_nurse_skill'] +=  max(0, skill_min_required - self.nurses[id_nurse].skill_level)
                            
                    # end for on room_vec
                    
                    # I have to dermine the max_load for a nurse by searching it in the dictionary
                    list_shift = self.nurses[id_nurse].working_shift
                    for elem in list_shift:
                        idx_x = 3*elem['day'] + elem['shift']
                        if idx_x == id_shift: max_workload = elem['max_load']
                        
                    weights_to_add['nurse_eccessive_workload'] += max(0, sum_workload - max_workload)
                                
            
        for set_of_nurses in set_of_nurse_par_people:
            weights_to_add['continuity_of_care'] += len(set_of_nurses)
            
        # computing the objective function
        value_obj = 0
        for key in weights_to_add.keys():
            value_obj += weights_to_add[key]*self.weights[key]
        
        if opt == 1:
            print(weights_to_add)
        
        return value_obj
            
            
    def generating_feasible_state(self):
        # I will generate a feasible state by creating a random scheduling for the nurses and then I will generate the dict_admission
        # To keep the generation process simple, all the non mandatory patients will not be accepted
        
        non_ho_ancora_generate_un_feasible_state = True
        
        while non_ho_ancora_generate_un_feasible_state:
            problem_copy = copy.deepcopy(self)
            
            # random generation of the dictionary of admission, that is the acceptance date, the OT and the assigned room
            dict_admission = {}
            for id_pat in problem_copy.patients.keys():
                
                # I begin by the mandatory patients
                if problem_copy.patients[id_pat].mandatory:

                    # for sake of simplicity, we will consider generate an acceptance date only among the ones feasible
                    date_possibili = set(range(problem_copy.patients[id_pat].surgery_release_day, problem_copy.patients[id_pat].surgery_due_day+1))                       
                    # we remove the dates in which the assigned surgeon does not work
                    for data, value in enumerate(problem_copy.surgeons[problem_copy.patients[id_pat].surgeon_id].max_surgery_time):
                        if value == 0 : 
                            try: date_possibili.remove(data)
                            except: pass

                    # random generation
                    data = random.choice(list(date_possibili))
                    
                    # the room is assigned among those which does not already contains people of the opposite gender and still have capacity
                    stanze_possibili  = set(range(problem_copy.hospital.n_rooms)) - set(problem_copy.patients[id_pat].incompatible_room_ids)
                    
                    for id_data_controllo in range(data, min([data+problem_copy.patients[id_pat].length_of_stay, problem_copy.days])):
                        for id_room in range(problem_copy.hospital.n_rooms):
                            # togliamo le stanze piene
                            if problem_copy.hospital.avalaibiity_per_room[id_data_controllo][id_room] <= 0: 
                                try: stanze_possibili.remove(id_room)
                                except: pass
                            # togliamo le stanze che contengono persone del sesso opposto
                            if not problem_copy.hospital.sesso_per_room[id_data_controllo][id_room] == problem_copy.patients[id_pat].gender  and  not problem_copy.hospital.sesso_per_room[id_data_controllo][id_room] == None:
                                try: stanze_possibili.remove(id_room)
                                except: pass
                        
                    # if stanze_possibili is an empty set, it won't be possible to random pick an elemnt out of it
                    try:
                        room = random.choice(list(stanze_possibili))  
                    except:
                        continue
                    
                    problem_copy.hospital.add_patient(room, data, problem_copy.patients[id_pat].length_of_stay, problem_copy.patients[id_pat].gender)    
                    dict_admission[id_pat] = [random.choice(list(problem_copy.hospital.capacity_per_OT.keys())), data, room]
                
            # for simplicity, non mandatory patients won't be admitted
            for id_pat in problem_copy.patients.keys():
                if not problem_copy.patients[id_pat].mandatory:
        
                    data = -1
                    room = None
                    
                    problem_copy.hospital.add_patient(room, data, problem_copy.patients[id_pat].length_of_stay, problem_copy.patients[id_pat].gender)    
                    dict_admission[id_pat] = [random.choice(list(problem_copy.hospital.capacity_per_OT.keys())), data, room]
            
            
            # Assignment of room to a nurse's shift
            # We are trying to do that in a way to create a feasible state while maintaing an compound of randomness:
            # - first we compute how many nurses are working in a given shift
            # - we distribute randomly the rooms among the nurses un a way that the assignements nurse-room are bijettive for each shift
            rooms_to_be_assigned = [[[] for _ in range(len(problem_copy.nurses[id_nurse].working_shift))] for id_nurse in problem_copy.nurses.keys()] 
                        
            
            for day in range(problem_copy.days):
                for shift in range(3):
                    # computing the number of nurses in the shift
                    lista_nurses = []
                    for nurse in problem_copy.nurses.keys():
                        if any([s['day'] == day and s['shift'] == shift for s in problem_copy.nurses[nurse].working_shift]):
                            lista_nurses.append(nurse)
                    
                    
                    # se ho 4 nurse che lavorano e 9 stanze assegno a tutte le nurse 2 stanze e all'ultima le 3 rimanenti
                    # se ho 4 nurse e 4 stanze --> 1 stanza a nurse
                    num_stanze_da_assegnare = problem_copy.hospital.n_rooms // len(lista_nurses)
                    room_tra_cui_scegliere = [i for i in range(problem_copy.hospital.n_rooms)]
                    cont = 0
                    
                    for idx, nurse in enumerate(problem_copy.nurses.keys()):
                        if nurse in lista_nurses: cont+=1
                        if not cont == len(lista_nurses):
                            for id_shift, s in enumerate(problem_copy.nurses[nurse].working_shift):
                                if s['day'] == day and s['shift'] == shift:
                                    
                                    # sampling the rooms to be assigned
                                    for _ in range(num_stanze_da_assegnare):
                                        room = random.choice(room_tra_cui_scegliere)
                                        room_tra_cui_scegliere.remove(room)
                                        rooms_to_be_assigned[idx][id_shift].append(room)
           
                        else:
                            # the last nurse is assigned to all the remaining rooms
                            for id_shift, s in enumerate(problem_copy.nurses[nurse].working_shift):
                                if s['day'] == day and s['shift'] == shift:
                                    rooms_to_be_assigned[idx][id_shift] = room_tra_cui_scegliere
                            
                                    
                            
            state = State(dict_admission, problem_copy.nurses, rooms_to_be_assigned, problem_copy.days)
            # checking if I created a feasible state
            if self.verifying_costraints(state):
                non_ho_ancora_generate_un_feasible_state = False
        
        return state
        
        
