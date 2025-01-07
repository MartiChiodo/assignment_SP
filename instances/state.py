import math

class State():
    
    def __init__(self, dict_admission, nurses, rooms_to_be_assigned, days):
        # nurses is the dictionare of all the nurses 
        self.dict_admission = dict_admission
        self.room_to_be_assigned = rooms_to_be_assigned
        self.nurses_shifts = self.creating_nurses_shifts_matrix(nurses, rooms_to_be_assigned, days)
        self.scheduling_OTs = self.defyning_scheduling_OTs(dict_admission, days)
    
    def adding_matrix(self, matrix):
        self.patients_per_room = matrix

        
    def creating_nurses_shifts_matrix(self, nurses, rooms_to_be_assigned, days):
        dict = {}
        for idx, (id_nurse, nurse) in enumerate(nurses.items()):
            # at first I create a list with all -1 then I am going to fill it with the rooms
            sched = [-1 for _ in range(3*days)]
            
            for id_shift, shift in enumerate(nurse.working_shift):
                id = 3*shift['day'] + shift['shift']
                sched[id] = rooms_to_be_assigned[idx][id_shift]
                
            dict[id_nurse] = sched
        
        return dict
    
    def defyning_scheduling_OTs(self,dict_admission, days):
        # I am creating a dictionary of list: at each OT I associate its scheduling 
        dict = {}
        
        # first I need the keys
        set_OTs = set()
        for elem in dict_admission.values():
            set_OTs.add(elem[0])
            
        for key in set_OTs:
            dict[key] = [[] for _ in range(days)]
            
        # filling the structure
        for key,elem in dict_admission.items():
            dict[elem[0]][elem[1]].append(key)
            
        return dict