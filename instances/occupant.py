import math
from .hospital import Hospital

class Occupant():
    def __init__(self, dict_occupant, hosp):
        for key, value in dict_occupant.items():
            setattr(self, key, value)
             
        # we are encoding the name of the room in natural numbers
        self.room_id = hosp.encoding_room(self.room_id)     
        hosp.add_patient(self.room_id, 0, self.length_of_stay)

        
    def encoding_agegroup(self, age_groups):
        mappatura = {elem: i for i, elem in enumerate(age_groups)}
        self.age_group = mappatura[self.age_group]