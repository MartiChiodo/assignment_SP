import copy
from instances.state import State
import random
import matplotlib.pyplot as plt


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
        for id_pat, value in state.dict_admission.items():
            if  value[1]  == -1:
                # se il paziente non è stato ammesso posso solo ammetterlo
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = min([random.randint(0, self.problem.days-1), self.problem.patients[id_pat].surgery_release_day])
                
                for id_room in range(self.problem.hospital.n_rooms):
                    new_dict[id_pat][2] = id_room
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
            else:
                # aggungo 1 alla data di ammissione
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = value[1] + 1 
                
                if  value[1] < (self.problem.days-1): 
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                
                # tolgo 1 alla data di ammissione
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = value[1]  - 1 
                
                if value[1] > 0: 
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                
                # se il paziente è non mandatory lo tolgo dall'ammissione
                if self.problem.patients[id_pat].mandatory == False:
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][1] = -1
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
            
            # scambio la stanza assegnata con un'altra stanza
            if not value[1] == -1:
                if value[2] > 0 and value[2] < self.problem.hospital.n_rooms -1 :
                    # stanza + 1
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][2] = value[2] + 1
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                    
                    # stanza -1
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][2] = value[2] - 1
                    new_state =State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                elif value[2] == 0:
                    # posso solo fare stanza + 1
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][2] = value[2] + 1
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                    
                elif value[2] == self.problem.hospital.n_rooms:
                    # posso solo fare stanza - 1
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][2] = value[2] - 1
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                
            # perturbazione sala operatoria --> ne scelgo una a caso da scambiare con quella attuale
            set_OTs = set(self.problem.hospital.capacity_per_OT.keys())
            new_dict = copy.deepcopy(state.dict_admission)
            new_dict[id_pat][0] = random.choice(list(set_OTs))
            neighborhoods.append(new_state)
            
            
        # II. perturbazione rooms_to_be_assigned --> ciclo sugli shift e se trovo due nurse che lavorano nello stesso turno scambio le loro stanze
        list_nurses = list(state.nurses_shifts.keys())
        for idx1 in range(len(list_nurses)):
            id_nurse1 = int(list_nurses[idx1][1:])
            for idx2 in range(idx1+1, len(list_nurses)):
                id_nurse2 = int(list_nurses[idx2][1:])
                for idx_shift in range(len(state.nurses_shifts[list_nurses[idx1]])):
                   if not (state.nurses_shifts[list_nurses[idx1]][idx_shift] == -1) and not (state.nurses_shifts[list_nurses[idx2]][idx_shift] == -1 ):
                       # ho trovato due infermiere che lavorano nello stesso turno, scambio le stanze a loro associate
                        new_state = copy.deepcopy(state)
                       
                       # indice_1 e indice_2 mi indicano il turno dell'infermiera in room_to_be_assigned
                        for id, elem in enumerate(state.room_to_be_assigned[id_nurse1]):
                            if elem == state.nurses_shifts[list_nurses[idx1]][idx_shift]: indice_1 = id
                            
                        for id, elem in enumerate(state.room_to_be_assigned[id_nurse2]):
                            if elem == state.nurses_shifts[list_nurses[idx2]][idx_shift]: indice_2 = id
                            
                        new_state.room_to_be_assigned[id_nurse1][indice_1] = state.nurses_shifts[list_nurses[idx1]][idx_shift]
                        new_state.room_to_be_assigned[id_nurse2][indice_2] = state.nurses_shifts[list_nurses[idx2]][idx_shift]
                        
                        neighborhoods.append(new_state)
                        
        return neighborhoods
            

    def solve(self, num_restart = 5, iter_max = 1000):
        problem = self.problem
        current_solution = self.initial_guess
        current_best_f = problem.objective_function(current_solution)
        
        best_solution_from_restart = []
        best_f_from_restart = []
        
        # Enable interactive mode
        plt.ion()

        # Initialize the plot
        fig, ax = plt.subplots()
        best_values = [current_best_f]
        line, = ax.plot(best_values, marker='o')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Best Value')
        ax.set_title('Best Value per Iteration')

        cont = 0    
        ho_un_miglioramento_nel_vicinato = True
        
        
        print('Prima iterazione dall\'initial guess ... ')
        f_neighbors = []
        best_neigh = current_solution
        best_neigh_f = current_best_f
        while cont < iter_max and ho_un_miglioramento_nel_vicinato: 
            ho_un_miglioramento_nel_vicinato = False
            neighbors = self.get_neighborhood(current_solution)
            # we apply the best improvement, exploring all the given neighborhood
            
            cont += 1
            
            print('Ho creato un vicinato ', end=' --> ')
            for idx, neig in enumerate(neighbors):
                if problem.verifying_costraints(neig): 
                    obj_fun = problem.objective_function(neig)
                    f_neighbors.append(obj_fun)
                    
                    # mi salvo se faccio un improvement
                    if obj_fun <= best_neigh_f:
                        ho_un_miglioramento_nel_vicinato = True
                        best_neigh = neig
                        best_neigh_f = obj_fun
                        
            if ho_un_miglioramento_nel_vicinato: print('il vicinato contiene un miglioramento.')
            else: print('il vicinato non contiene nessun miglioramento.')
            
            best_values.append(best_neigh_f)
                        
            # Update the plot
            line.set_ydata(best_values)
            line.set_xdata(range(len(best_values)))
            ax.relim()
            ax.autoscale_view()
            plt.draw()
            plt.pause(0.01)

                 
        # I store the best values to compare them at the end of the search               
        best_solution_from_restart.append(best_neigh)
        best_f_from_restart.append(best_neigh_f)
        
        print('\n')        
        print('Generazione nuovi punti di partenza ... ')       
        # we restart the search from the a random solution
        for id_restart in range(num_restart):
            print(f'\n {id_restart} -esimo restart ... ')
            
            # aggiungo una riga rossa verticale al plot 
            plt.axvline(x=len(best_values), color='red', linestyle='--', label="Restart")

            # generate a random solution
            current_solution = problem.generating_feasible_state()
            current_best_f = problem.objective_function(current_solution)
            
            cont = 0
            ho_un_miglioramento_nel_vicinato = True
            
            f_neighbors = []
            best_neigh = current_solution
            best_neigh_f = current_best_f
            
            while cont < iter_max and ho_un_miglioramento_nel_vicinato: 
                ho_un_miglioramento_nel_vicinato = False
                neighbors = self.get_neighborhood(current_solution)
                
                cont += 1
                
                print('Ho creato un vicinato ', end=' --> ')
                for idx, neig in enumerate(neighbors):
                    if problem.verifying_costraints(neig): 
                        obj_fun = problem.objective_function(neig)
                        f_neighbors.append(obj_fun)
                        
                        # mi salvo se faccio un improvement
                        if obj_fun <= best_neigh_f:
                            ho_un_miglioramento_nel_vicinato = True
                            best_neigh = neig
                            best_neigh_f = obj_fun
                            
                            
                if ho_un_miglioramento_nel_vicinato: print('il vicinato contiene un miglioramento.')
                else: print('il vicinato non contiene nessun miglioramento.')
                            
                best_values.append(best_neigh_f)
                        
                # Update the plot
                line.set_ydata(best_values)
                line.set_xdata(range(len(best_values)))
                ax.relim()
                ax.autoscale_view()
                plt.draw()
                plt.pause(0.01)
                            
            # I store the best values to compare them at the end of the search               
            best_solution_from_restart.append(best_neigh)
            best_f_from_restart.append(best_neigh_f)
                    
            


        # I return the best solution found
        best_solution = best_solution_from_restart[best_f_from_restart.index(min(best_f_from_restart))]
        best_f = min(best_f_from_restart)
        
        return best_solution, best_f 


    

    
