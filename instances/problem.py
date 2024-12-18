import math

class Problem():
    
    def __init__(self):
        self.constraints = []
        self.variables = []
        
        # DECISIONAL VARIABLES and COSTRAINTS
        #   - for each patients, the admission date (negative values for optional patient for postponed scheduling period)
        #       I. for mandatory patients, admision date > 0 and release_date <= admission <= due_date
        #       II. for optional patients, release_date <= admission (the others became soft costraints --> penalize in obj func)
        #   - for each patients, the allocation of the room (-1 patient has not been accepted)
        #       I. room_id should not be in the list of incopatible_id
        #       II. be careful on capacity costraints on rooms
        #       III. people of different genders cannot be in the same room
        #   - for each nurse, a vector 1x(3*dayx), where the i-th element indicates in which room she is working (-1 if she is not working)
        #       I.  all costraints about assigning a nurse to a room are soft costraints --> penalize on the obj function
        #       II. we need to check that there are negative values on the shifts she is not working
        #       III. we need to check that each non-empty room has assigned a nurse
        #   - a matrix (num_patients) x 2 in which the i-th row contains the info about in which OT the patient i is operated and in which day 
        #       I. verifying that the capacities about OTs and surgeons are satisfied
        
        
    def add_variable(self, variable):
        if len(variable) > 1:
            for elem in variable:
                self.variables.append(elem)
            else:
                self.variables.append(variable)
        
    def add_costraint(self, costraint):
        pass
    
    