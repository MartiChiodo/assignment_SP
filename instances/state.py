import math
from .problem import Problem

class State():
    
    def __init__(self, dict_admission, nurses_shifts):
        self.dict_admission = dict_admission
        self.nurses_shifts = nurses_shifts
    
    def adding_matrix(self, matrix):
        self.patients_per_room = matrix

        
        