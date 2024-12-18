import math
import numpy as np

class Hospital():

    def __init__(self, rooms_listofdict, ot_listofdict, days):
        self.n_rooms = len(rooms_listofdict)
        self.occupation = np.zeros((days, self.n_rooms))
        self.capacity_per_room = np.zeros(self.n_rooms)
        for i in range(self.n_rooms):
            self.capacity_per_room[i] = rooms_listofdict[i]['capacity']
        
        self.n_operating_theatres = len(ot_listofdict)
        self.avalaibility = np.zeros((self.n_operating_theatres, days))
        for i in range(self.n_operating_theatres):
            self.avalaibility[i] = ot_listofdict[i]['availability']
        
        self.days = days
        
        self.mappatura = {elem['id']: i for i, elem in enumerate(rooms_listofdict)}
    
    def add_patient(self, idx_room, acceptance_date, lenght_stay):
        for i in range(lenght_stay):
            row = min(acceptance_date + i, self.days)
            self.occupation[row][idx_room] += 1
        
    def define_avalaibility(self, idx_ot, avalaibility_ot):
        self.avalaibility[idx_ot] = avalaibility_ot
        
    def encoding_room(self, id_room):
        return self.mappatura[id_room]


