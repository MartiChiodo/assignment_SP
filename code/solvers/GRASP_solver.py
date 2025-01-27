import copy
from instances.state import State
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class GRASP_Solver():
    def __init__(self, problem, initial_guess):
        self.problem = problem
        self.initial_guess = initial_guess
        
    def get_neighborhood(self, state):
        neighborhoods = []
        # state is the current value of all the decisional variables
        
        # I. perturbation dict_admission
        for id_pat, value in state.dict_admission.items():
            # value = [id_ot, acceptance_date, id_room]
            if  value[1]  == -1:
                # if the patient have not been accepted I can assign him an acceptance_date and a room
                for data in range(self.problem.patients[id_pat].surgery_release_day, self.problem.days):
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][1] = data
                    
                    for id_room in range(self.problem.hospital.n_rooms):
                        for id_OT in self.problem.hospital.capacity_per_OT.keys():
                            new_dict[id_pat][2] = id_room
                            new_dict[id_pat][0] = id_OT
                            new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                            neighborhoods.append(new_state)
                        
                        
            else:
                # adding 1 to the admission_date
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = value[1] + 1 
                
                if  value[1] < (self.problem.days-1): 
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                
                # subtracting 1 to the admission_date
                new_dict = copy.deepcopy(state.dict_admission)
                new_dict[id_pat][1] = value[1]  - 1 
                
                if value[1] > 0: 
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                
                # if patient is not mandatory, I reject him
                if self.problem.patients[id_pat].mandatory == False:
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][1] = -1
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
            
            # changes in room
            if not value[1] == -1:
                if value[2] > 0 and value[2] < self.problem.hospital.n_rooms -1 :
                    # room + 1
                    new_dict = copy.deepcopy(state.dict_admission)
                    new_dict[id_pat][2] = value[2] + 1
                    new_state = State(new_dict, self.problem.nurses, state.room_to_be_assigned, self.problem.days)
                    neighborhoods.append(new_state)
                    
                    # room -1
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
                
            # randomly changing the OT assigned to a patient
            set_OTs = set(self.problem.hospital.capacity_per_OT.keys())
            new_dict = copy.deepcopy(state.dict_admission)
            new_dict[id_pat][0] = random.choice(list(set_OTs))
            neighborhoods.append(new_state)
            
            
        # II. perturbation of  rooms_to_be_assigned 
        # If I identify 2 nurses who are working on the same shift I swap the rooms assigned to them
        list_nurses = list(state.nurses_shifts.keys())
        for idx1 in range(len(list_nurses)):
            id_nurse1 = int(list_nurses[idx1][1:])
            for idx2 in range(idx1+1, len(list_nurses)):
                id_nurse2 = int(list_nurses[idx2][1:])
                for idx_shift in range(len(state.nurses_shifts[list_nurses[idx1]])):
                   if not (state.nurses_shifts[list_nurses[idx1]][idx_shift] == -1) and not (state.nurses_shifts[list_nurses[idx2]][idx_shift] == -1 ):
                       # I found two nurses working on the same shift
                        new_state = copy.deepcopy(state)
                       
                       # indice_1 and indice_2 are the index of the nurses in the data structure room_to_be_assigned
                        for id, elem in enumerate(state.room_to_be_assigned[id_nurse1]):
                            if elem == state.nurses_shifts[list_nurses[idx1]][idx_shift]: indice_1 = id
                            
                        for id, elem in enumerate(state.room_to_be_assigned[id_nurse2]):
                            if elem == state.nurses_shifts[list_nurses[idx2]][idx_shift]: indice_2 = id
                            
                        new_state.room_to_be_assigned[id_nurse1][indice_1] = state.nurses_shifts[list_nurses[idx1]][idx_shift]
                        new_state.room_to_be_assigned[id_nurse2][indice_2] = state.nurses_shifts[list_nurses[idx2]][idx_shift]
                        
                        neighborhoods.append(new_state)
                        
        return neighborhoods
            

    def solve(self, num_restart=5, iter_max_cost=50):
        problem = self.problem
        current_solution = self.initial_guess
        current_best_f = problem.objective_function(current_solution)

        best_solution_from_restart = []
        best_f_from_restart = []
        best_values = [current_best_f]  # Track the best values for the plot
        restart_points = []  # Track the iteration indices where restarts happen

        # Optimization Loop
        cont = 0
        ho_un_miglioramento_nel_vicinato = True
        print("Prima iterazione dall'initial guess ... ")
        while cont < iter_max_cost and ho_un_miglioramento_nel_vicinato:
            ho_un_miglioramento_nel_vicinato = False
            neighbors = self.get_neighborhood(current_solution)

            print('Ho creato un vicinato ', end=' --> ')
            for idx, neig in enumerate(neighbors):
                if problem.verifying_costraints(neig):
                    obj_fun = problem.objective_function(neig)
                    if obj_fun < current_best_f:
                        ho_un_miglioramento_nel_vicinato = True
                        current_solution = neig
                        current_best_f = obj_fun
                        cont = 0
                    elif obj_fun <= current_best_f:
                        ho_un_miglioramento_nel_vicinato = True
                        current_solution = neig
                        current_best_f = obj_fun
                        cont += 1

            if ho_un_miglioramento_nel_vicinato:
                print('il vicinato contiene un miglioramento, fbest = ', current_best_f)
            else:
                print('il vicinato non contiene nessun miglioramento.')

            # Update the best values for the plot
            best_values.append(current_best_f)

        # Store the best results from this restart
        best_solution_from_restart.append(current_solution)
        best_f_from_restart.append(current_best_f)

        print('\nGenerazione nuovi punti di partenza ... ')
        for id_restart in range(num_restart):
            print(f'\n {1 + id_restart}-esimo restart ... ')

            # Track the restart point for plotting
            restart_points.append(len(best_values))

            # Generate a new random solution
            current_solution = problem.generating_feasible_state()
            current_best_f = problem.objective_function(current_solution)
            cont = 0
            ho_un_miglioramento_nel_vicinato = True

            while cont < iter_max_cost and ho_un_miglioramento_nel_vicinato:
                neighbors = self.get_neighborhood(current_solution)

                cont += 1

                ho_un_miglioramento_nel_vicinato = False
                print('Ho creato un vicinato ', end=' --> ')
                for idx, neig in enumerate(neighbors):
                    if problem.verifying_costraints(neig):
                        obj_fun = problem.objective_function(neig)
                        if obj_fun < current_best_f:
                            ho_un_miglioramento_nel_vicinato = False
                            current_solution = neig
                            current_best_f = obj_fun
                            cont = 0
                        elif obj_fun <= current_best_f:
                            ho_un_miglioramento_nel_vicinato = True
                            current_solution = neig
                            current_best_f = obj_fun
                            cont += 1

                if ho_un_miglioramento_nel_vicinato:
                    print('il vicinato contiene un miglioramento, fbest = ', current_best_f)
                else:
                    print('il vicinato non contiene nessun miglioramento.')

                # Update the best values for the plot
                best_values.append(current_best_f)
                
            # Store the best results from this restart
            best_solution_from_restart.append(current_solution)
            best_f_from_restart.append(current_best_f)

        # Final plot update and adjustment
        plt.figure(figsize=(8, 6))
        plt.plot(best_values, 'b-o', label="Best Objective Value")
        
        # Optional: Add vertical lines for restart points
        for restart in restart_points:
            plt.axvline(x=restart, color='red', linestyle='--', label="Restart Point")

        # Set plot labels and title
        plt.xlabel("Iterations")
        plt.ylabel("Objective Value")
        plt.title("Optimization Progress")

        # # Save the plot as a PDF or PNG
        plt.savefig('optimization_plot.pdf', bbox_inches='tight')  # Save as PDF
        
        # Show the plot
        plt.show()

        # Return the overall best solution
        best_solution = best_solution_from_restart[best_f_from_restart.index(min(best_f_from_restart))]
        best_f = min(best_f_from_restart)
        return best_solution, best_f
