import numpy as np
import random
from person import Person

# np.random.seed(42)

# Grid
grid_width = 100
grid_height = 100
initial_pop_size = 1
number_iterations = 20

# Person Initial Attributes
age_range = [10, 80]  # Range
movement_prob = {'low': 0.25, 'high': 0.75}  # Choices (prob. of moving that step)
initial_infection_prob = 1.  # ie on avg X% of people will start out infected
altruistic_prob = 0.8  # Prob that someone who has symptoms will wear a mask and social distance

# Person Disease Attributes
# Prob. that an infected person (right next to) will infect a susceptible person
base_infection_prob = 0.1  # Not based on any stats
# This is how much the base_infection_prob is lowered if the infected individual is wearing a mask
mask_infection_prob_decrease = 0.05  # Not based on any stats
# Total length of infection in days
total_length_infection = 14  # REF 3
# Length range of the incubation period
incubation_period_duration_range = [4, 6]  # REF 3
# Length range of infectious period
infectious_period_duration_range = [8, 9]  # REF 3
# How many days before symptoms show (or would show if asymptomatic) would infectious start
infectious_start_before_symptoms_range = [2, 3]  # REF 3
# Starting at each age given (keys): values are the prob for severe (o.w. mild)
severity_by_age = [(10, 0.05), (20, 0.1), (40, 0.2), (60, 0.4)]  # Based off of REF 8 (but I had to make up some things)

severity_prob = 0.5

# How long after showing symptoms would severe symptoms (if they are gonna show up) start
severe_symptoms_start_range = [2, 4]  # todo: GET REAL DATA FOR THIS
# How long after showing severe symptoms does death usually occur
death_occurrence_range = [2, 4]  # todo: GET REAL DATA FOR THIS
asymptomatic_prob = 0.2  # REF 1 (0.35)
# The prob of death GIVEN severe symptoms (by age in the same way as severity by age)
# Since dying is a subset of severe (only people who had severe symptoms died) then its just fatality (given by REF 8)
# divided by severity by age (which I made up but is still based off of REF 8)
case_fatality_rate_by_age_given_severe_symptoms = [(10, 0.04), (20, 0.02), (40, 0.02), (50, 0.065), (60, 0.2), (70, 0.37)]

death_prob = 0.5

# todo: add a testing policy!!!!!
policies_safety = {
    'high': {'social_distance_prob': 0.75, 'wear_mask_prob': 0.75, 'low_movement_prob': 0.75},
    'medium': {'social_distance_prob': 0.5, 'wear_mask_prob': 0.5, 'low_movement_prob': 0.5},
    'low': {'social_distance_prob': 0.25, 'wear_mask_prob': 0.25, 'low_movement_prob': 0.25},
}
policy_type = 'medium'

# Virus/Disease Attributes (COVID-19)


class CellularAutomation:
    def __init__(self):
        # Need two sets of ids (correspond uniquely to a person)
        # 1) Those who practice social distancing
        # 2) Those who do not practice social distancing
        self.ids_social_distance = set()
        self.ids_not_social_distance = set()
        # The person objects
        # id (int): person (object)
        self.id_person = {}
        self.grid = np.empty(shape=(grid_height, grid_width), dtype=np.object)
        self.next_id = 0
        # The currently open positions (no person on it)
        self.open_positions = []
        for y in range(grid_height):
            for x in range(grid_width):
                self.open_positions.append((x, y))
        # Initialize the grid
        self._initialize_grid()

    # Out of bounds
    def _oob(self, x, y):
        return x < 0 or y < 0 or x >= grid_width or y >= grid_height

    # Env wraps so get correct pos
    def _get_cell_pos(self, x, y):
        def corrected(val, max_val):
            if val < 0:
                 return max_val + val
            elif val >= max_val:
                return max_val - val
            else:
                return val
        return corrected(x, grid_width), corrected(y, grid_height)

    def _is_empty(self, x=None, y=None, position=None):
        if x and y:
            return self.grid[y, x] is None
        return self.grid[position[1], position[0]] is None

    def _kill_person(self, id, social_distance):
        if social_distance: self.ids_social_distance.remove(id)
        else: self.ids_not_social_distance.remove(id)
        position = self.id_person[id].position
        self._clear_cell(position)
        del self.id_person[id]

    def _clear_cell(self, position):
        self.grid[position[1], position[0]] = None
        self.open_positions.append(position)

    def _add_to_cell(self, id, position):
        assert self._is_empty(position=position)
        self.id_person[id].position = position
        self.grid[position[1], position[0]] = id
        self.open_positions.remove(position)

    def _move_person(self, id, person, new_position):
        # assert self._is_empty(position=new_position)
        current_position = person.position
        # Clear current position
        self._clear_cell(current_position)
        # Place person in new cell
        self._add_to_cell(id, new_position)
        person.set_position(new_position)

    # Grid initialization ------
    def _create_person(self, position):
        assert self._is_empty(position=position)
        age = np.random.randint(age_range[0], age_range[1]+1)
        policy = policies_safety[policy_type]
        SD_prob = policy['social_distance_prob']
        SD = True if np.random.random() < SD_prob else False
        WM_prob = policy['wear_mask_prob']
        WM = True if np.random.random() < WM_prob else False
        LM_prob = policy['low_movement_prob']
        LM = movement_prob['low'] if np.random.random() < LM_prob else movement_prob['high']
        infected = np.random.random() < initial_infection_prob
        def get_prob_by_age(arr):
            for age_prob in arr:
                age_min, prob = age_prob[0], age_prob[1]
                if age >= age_min:
                    return prob
            raise AssertionError('age {} not correct'.format(age))
        # person = Person(position, age, SD, WM, LM, movement_prob['low'], altruistic_prob, infected,
        #                 total_length_infection, incubation_period_duration_range,
        #                 infectious_start_before_symptoms_range, infectious_period_duration_range, severe_symptoms_start_range,
        #                 death_occurrence_range, asymptomatic_prob, get_prob_by_age(severity_by_age),
        #                 get_prob_by_age(case_fatality_rate_by_age_given_severe_symptoms))

        person = Person(position, age, SD, WM, LM, movement_prob['low'], altruistic_prob, infected,
                        total_length_infection, incubation_period_duration_range,
                        infectious_start_before_symptoms_range, infectious_period_duration_range, severe_symptoms_start_range,
                        death_occurrence_range, asymptomatic_prob, severity_prob,
                        death_prob)

        self.id_person[self.next_id] = person
        if SD: self.ids_social_distance.add(self.next_id)
        else: self.ids_not_social_distance.add(self.next_id)
        self._add_to_cell(self.next_id, position)
        self.next_id += 1

    # Create all the people
    def _initialize_grid(self):
        for p in range(initial_pop_size):
            # Select random position
            position = random.choice(self.open_positions)
            # Create person
            self._create_person(position)

    # Yield neighbors
    # Return Neighbor (or None), neighbor_position
    def _yield_neighbors(self, position, side_length):
        x, y = position[0], position[1]
        for i in range(side_length ** 2):
            cluster_mid = side_length // 2
            rel_x = (i % side_length) - cluster_mid
            rel_y = (i // side_length) - cluster_mid
            # imm_neighbor = True if (rel_x, rel_y) in [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (1, -1), (-1, -1), (1, 1)] else False
            abs_x = x + rel_x
            abs_y = y + rel_y
            correct_x, correct_y = self._get_cell_pos(abs_x, abs_y)
            located_id = self.grid[correct_y, correct_x]  # Might be None if no person there
            if located_id == None:
                yield None, (correct_x, correct_y), (rel_x, rel_y)
            else:
                yield self.id_person[located_id], (correct_x, correct_y), (rel_x, rel_y)

    # This decides movement and num of infected neighbors FOR SD people
    def _check_neighbors_SD(self, person):
        safe_cells = {(-1, -1): None, (0, -1): None}
        num_infected = 0
        for neighbor, neighbor_pos, neighbor_pos_rel in self._yield_neighbors(person.position, 3):
            if neighbor_pos == person.position:
                continue
            # Get abs pos
            safe_cells[neighbor_pos_rel] = neighbor_pos
            # Add to infected if infectious neighbor IN 3x3
            if neighbor and neighbor.is_infectious() and neighbor_pos != person.position:
                num_infected += 1
            # Remove from safe cell if cell contains a person
            if neighbor and neighbor_pos_rel in safe_cells:
                del safe_cells[neighbor_pos_rel]
        # Move it if its own cell is not safe OR its moving intenionally
        if len(safe_cells) < 8 or np.random.random() < person.movement_prob:
            # Shuffle the safe positions and choose the first actually safe one by checking a 3x3 around it (not including the person.position)
            for safe_cell_rel_pos in random.sample(list(safe_cells.keys()), len(list(safe_cells.keys()))):
                safe_cell_abs_pos = safe_cells[safe_cell_rel_pos]
                # Check if its safe (dont check the person.position)
                safe = True
                for neighbor, neighbor_pos, _ in self._yield_neighbors(safe_cell_abs_pos, 3):
                    if neighbor_pos == person.position:
                        continue
                    if neighbor:
                        safe = False
                        break
                if safe:
                    return safe_cell_abs_pos, num_infected
        return person.position, num_infected

    # If not SD then move if moving intentionally
    def _check_neighbors_not_SD(self, person):
        empty_spots = []
        num_infected = 0
        for neighbor, neighbor_pos, _ in self._yield_neighbors(person.position, 3):
            if neighbor_pos == person.position:
                continue
            # Add to infected if infectious neighbor
            if neighbor and neighbor.is_infectious():
                num_infected += 1
            # Add empty spot
            if not neighbor:
                empty_spots.append(neighbor_pos)
        new_spot = random.choice(empty_spots) if len(empty_spots) > 0 else person.position
        return num_infected, new_spot

    def _update_person(self, id):
        person = self.id_person[id]
        # At the start figure out where the person is going to move AND the number of infected persons around them
        new_position, num_infected = self._check_neighbors_SD(person) if person.social_distance else self._check_neighbors_not_SD(person)
        # Progress Infection (if infected)
        dead, new_SD = person.progress_infection()
        if dead:
            self._kill_person(id, person.social_distance)
            return  # Continue to next person
        # Infect (if susceptible)
        person.gets_infected(num_infected, base_infection_prob, mask_infection_prob_decrease)
        # Move
        # if new_position != person.position: self._move_person(id, person, new_position)
        return new_SD

    def run(self):
        for t in range(number_iterations):
            def loop_through_ids(ids):
                # Keep track of any switches between SD lists
                new_SD_list = []
                new_not_SD_list = []
                # Shuffle - Random order
                lis = list(ids)
                random.shuffle(lis)
                for id in lis:
                    new_SD = self._update_person(id)
                    if new_SD is True: new_SD_list.append(id)
                    elif new_SD is False: new_not_SD_list.append(id)
                return new_SD_list, new_not_SD_list
            # Update (in random order) those who do NOT practice social distancing
            new_SD, new_not_SD_list = loop_through_ids(self.ids_not_social_distance)
            assert len(new_not_SD_list) == 0
            # Next update (in random order) those who DO practice social distancing, so they get to be at a safe dist.
            # from others at the end of the iteration
            new_SD_list, new_not_SD = loop_through_ids(self.ids_social_distance)
            assert len(new_SD_list) == 0
            # Switch people
            for id in new_SD:
                self.ids_not_social_distance.remove(id)
                self.ids_social_distance.add(id)
            for id in new_not_SD:
                self.ids_social_distance.remove(id)
                self.ids_not_social_distance.add(id)

CA = CellularAutomation()
CA.run()