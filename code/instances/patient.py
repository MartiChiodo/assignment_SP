import math
import numpy as np
from .hospital import Hospital

class Patient():

    def __init__(self, dict_patient, hospital):
        for key, value in dict_patient.items():
            setattr(self, key, value)
            
        # encoding the name room as integer numbers
        self.hosp = hospital
        self.incompatible_room_ids = [hospital.encoding_room(elem) for elem in self.incompatible_room_ids ]

        
    def encoding_agegroup(self, age_groups):
        mappatura = {elem: i for i, elem in enumerate(age_groups)}
        self.age_group = mappatura[self.age_group]
        return self
        

        
