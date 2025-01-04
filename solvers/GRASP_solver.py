
class GRASP_Solver():
    def __init__(self, problem, initial_guess):
        self.problem = problem
        self.initial_guess = initial_guess
        
    def get_neighborhood(self, state):
        # state is the currente values of all the decisional variables
        
        # I. perturbazione stanze/date ammissioni pazienti controllando un minimo i vincoli
        # II. scambiare le stanze tra le infermiere che lavorano nello stesso shift
        # III. for optional patients nel vicinato metti anche l'opzione di non operarlo

        neighborhoods = []
        
        
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
    

    
