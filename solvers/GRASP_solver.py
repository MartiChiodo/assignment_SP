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
                        
        return neighborhoods
            

    def solve(self, problem, num_restart = 5, iter_max = 100):
        current_solution = self.initial_guess
        current_best_f = problem.objective_function(current_solution)
        
        best_solution_from_restart = []
        best_f_from_restart = []

        
        for _ in range(iter_max): 
            neighbors = self.get_neighborhood(current_solution)
            # we apply the best improvement, exploring all the given neighborhood
            f_neighbors = []
            best_neigh = current_solution
            best_neigh_f = current_best_f
            
            for idx, neig in enumerate(neighbors):
                if problem.verifying_constraints(neig): 
                    obj_fun = problem.objective_function(neig)
                    f_neighbors.append(obj_fun)
                    
                    # mi salvo se faccio un improvement
                    if obj_fun <= best_neigh_f:
                        best_neigh = neig
                        best_neigh_f = obj_fun
                
        # I store the best values to compare them at the end of the search               
        best_solution_from_restart.append(best_neigh)
        best_f_from_restart.append(best_neigh_f)
                
                 
        # we restart the search from the a random solution
        for _ in range(num_restart):
            # generate a random solution
            current_solution = problem.generating_feasible_state()
            current_best_f = problem.objective_function(current_solution)
            
            for _ in range(iter_max): 
                neighbors = self.get_neighborhood(current_solution)
                # we apply the best improvement, exploring all the given neighborhood
                f_neighbors = []
                best_neigh = current_solution
                best_neigh_f = current_best_f
                
                for idx, neig in enumerate(neighbors):
                    if problem.verifying_constraints(neig): 
                        obj_fun = problem.objective_function(neig)
                        f_neighbors.append(obj_fun)
                        
                        # mi salvo se faccio un improvement
                        if obj_fun <= best_neigh_f:
                            best_neigh = neig
                            best_neigh_f = obj_fun
                            
            # I store the best values to compare them at the end of the search               
            best_solution_from_restart.append(best_neigh)
            best_f_from_restart.append(best_neigh_f)
                    
                    
                    
        # we restart a last time from the best solution found
        current_solution = best_solution_from_restart[best_f_from_restart.index(min(best_f_from_restart))]
        current_best_f = min(best_f_from_restart)
        
        for _ in range(iter_max): 
            neighbors = self.get_neighborhood(current_solution)
            # we apply the best improvement, exploring all the given neighborhood
            f_neighbors = []
            best_neigh = current_solution
            best_neigh_f = current_best_f
            
            for idx, neig in enumerate(neighbors):
                if problem.verifying_constraints(neig): 
                    obj_fun = problem.objective_function(neig)
                    f_neighbors.append(obj_fun)
                    
                    # mi salvo se faccio un improvement
                    if obj_fun <= best_neigh_f:
                        best_neigh = neig
                        best_neigh_f = obj_fun
                          
        # I store the best values to compare them at the end of the search               
        best_solution_from_restart.append(best_neigh)
        best_f_from_restart.append(best_neigh_f)
            


        # I return the best solution found
        best_solution = best_solution_from_restart[best_f_from_restart.index(min(best_f_from_restart))]
        best_f = min(best_f_from_restart)
        
        return best_solution, best_f 


    

    
