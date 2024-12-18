import math

class Surgeon():

    def __init__(self, dict_surgeon):
        self.id = dict_surgeon['id']
        self.max_surgery_time = dict_surgeon['max_surgery_time']