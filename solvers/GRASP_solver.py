import copy
from instances.state import State
import random


class GRASP_Solver():
    def __init__(self, problem, initial_guess):
        self.problem = problem
        self.initial_guess = initial_guess
        
    def get_neighborhood(self, state):
        neighborhoods = []
        # state is the currente values of all the decisional variables
        
        # I. perturbazione stanze/date ammissioni pazienti controllando un minimo i vincoli
        # II. scambiare le stanze tra le infermiere che lavorano nello stesso shift
        # III. for optional patients nel vicinato metti anche l'opzione di non operarlo
        
        # I. perturbazione dict_admission
        for id_pat, value in state.dict_adission.items():
            if  value[1]  == -1:
                # se il paziente non è stato ammesso posso solo ammetterlo
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = min([random.randint(0, self.days-1), self.problem.patients[id_pat].surgery_release_day])
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                neighborhoods.append(new_state)
            else:
                # aggungo 1 alla data di ammissione
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = value[1] +1 
                
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                if  value[1] +1 < self.days: neighborhoods.append(new_state)
                
                # tolgo 1 alla data di ammissione
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = value[1]  - 1 
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                if value[1] > 0: neighborhoods.append(new_state)
                
                # se il paziente è non mandatory lo tolgo dall'ammissione
                if self.problem.patients[id_pat].mandatory == False:
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][1] = -1
                    new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                    neighborhoods.append(new_state)
            
            # scambio la stanza assegnata con un'altra stanza
            if value[2] > 0 and value[2] < self.problem.hospital.num_rooms -1 :
                # stanza + 1
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][2] = value[2] + 1
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                neighborhoods.append(new_state)
                
                # stanza -1
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][2] = value[2] - 1
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                neighborhoods.append(new_state)
            elif value[2] == 0:
                # posso solo fare stanza + 1
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][2] = value[2] + 1
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                neighborhoods.append(new_state)
                
            elif value[2] == self.problem.hospital.num_rooms:
                # posso solo fare stanza - 1
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][2] = value[2] - 1
                new_state = State(self.problem.nurses, new_dict, state.rooms_to_be_assigned, state.days)
                neighborhoods.append(new_state)
                
            # perturbazione sala operatoria --> ne scelgo una a caso da scambiare con quella attuale
            set_OTs = set(self.problem.hospital.avalaibilityOT.keys())
            new_dict = copy.deepcopy(state.dict_admission)
            new_dict[id_pat][0] = random.choice(list(set_OTs))
            neighborhoods.append(new_state)
            
            
        # II. perturbazione rooms_to_be_assigned --> ciclo sugli shift e se trovo due nurse che lavorano nello stesso turno scambio le loro stanze
        list_nurses = list(state.nurses_shifts.keys())
        for idx1 in range(len(list_nurses)):
            for idx2 in range(idx1+1, len(list_nurses)):
               for idx_shift in range(len(state.nurses_shifts[list_nurses[idx1]])):
                   if not (state.nurses_shifts[list_nurses[idx1]][idx_shift] == -1 and state.nurses_shifts[list_nurses[idx2]][idx_shift] == -1 ):
                       # ho trovato due infermiere che lavorano nello stesso turno, scambio le stanze a loro associate
                        new_state = copy.deepcopy(state)
                       
                        indice_room_1 = (state.rooms_to_be_assigned[idx1]).find(state.nurses_shifts[list_nurses[idx1]][idx_shift])
                        indice_room_2 = (state.rooms_to_be_assigned[idx2]).find(state.nurses_shifts[list_nurses[idx2]][idx_shift])
                        
                        new_state.rooms_to_be_assigned[idx1]= state.rooms_to_be_assigned[idx2][indice_room_2]
                        new_state.rooms_to_be_assigned[idx2]= state.rooms_to_be_assigned[idx1][indice_room_1]
                        
                        neighborhoods.append(new_state)
                       
        
        pass

    def solve(self, problem):
        current_solution = self.initial_guess
        current_best_f = problem.objective_function(current_solution)
        max_iter = 10 # number of starting solutions from which we apply local search
        best_solution = current_solution
        best_f = current_best_f
        
        for outer_iter in range(max_iter): 
            neighbors = self.get_neighborhood(current_solution)
            # we apply the best improvement, exploring all the given neighborhood
            f_neighbors = []
            for idx, neig in enumerate(neighbors):
                if problem.verifying_constraints(neig): f_neighbors.append(problem.objective_function(neig))
                else: del neighbors[idx]
                
            min_value = min(f_neighbors)
            if min_value <= current_best_f: 
                current_solution = neighbors.index(min_value)
                current_best_f = min_value
            else: 
                 # as we are starting from scratch we don't want to throw away the current best, in case we won't find anything better
                 best_solution = current_solution
                 best_f = current_best_f 
                 # generation of a new starting point if no improvement has been found
                 # QUESTO LO FACCIAMO COME? MODIFICHIAMO LA SOLUZIONE CORRENTE IN MODO RANDOM FINCHE' NON SODDISFA I VINCOLI O E' TROPPO LUNGO?

        if best_f < current_best_f: solution = best_solution
        else: solution = current_solution

        return solution 

        pass
    

    
