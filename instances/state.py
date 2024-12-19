import math

class State():
    
    def __init__(self, dict_admission, patients_per_room, nurses_shifts):
        self.dict_admission = dict_admission
        self.patients_per_room = patients_per_room
        self.nurses_shifts = nurses_shifts
        
        