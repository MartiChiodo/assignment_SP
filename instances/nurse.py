import math

class Nurse():

    def __init__(self, dict_nurse):
        # working_shift is a dictionary of dictionary built as in the JSON file
        self.id = dict_nurse['id']
        self.skill_level = dict_nurse['skill_level']
        
        # before storing the working shift infos we map ['early', 'late', 'night'] --> [0,1,2]
        mapp = {'early' : 0, 'late': 1, 'night':2}
        
        for elem in dict_nurse['working_shifts']:
            elem['shift'] = mapp[elem['shift']]
        
        
        self.working_shift = dict_nurse['working_shifts']
       
    
        
        

