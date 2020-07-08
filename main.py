import numpy as np
import random
from person import Person
import pygame
from data_collector import DataCollector

# np.random.seed(42)

# Grid
grid_width = 75
grid_height = 75
initial_pop_size = 500
number_iterations = 50

# Render
cell_size = 8
screen_height = grid_height * cell_size
screen_width = grid_width * cell_size
color_models = {'SIR': {'susceptible': (204, 255, 204), 'infected': (255, 204, 204), 'recovered': (204, 204, 255)}}
current_color_model = 'SIR'
fps = 3

# Person Initial Attributes
age_range = [10, 80]  # Range
movement_prob = {'low': 0.25, 'high': 0.75}  # Choices (prob. of moving that step)
move_length = 6  # Number of cells to move in a single step
initial_infection_prob = 0.05  # ie on avg X% of people will start out infected
altruistic_prob = 0.75  # Prob that someone who has symptoms will wear a mask and social distance

# Person Disease Attributes
# Prob. that an infected person (right next to) will infect a susceptible person
base_infection_prob = 0.5  # Not based on any stats
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

severity_prob = 0.25

# How long after showing symptoms would severe symptoms (if they are gonna show up) start
severe_symptoms_start_range = [2, 4]  # todo: GET REAL DATA FOR THIS
# How long after showing severe symptoms does death usually occur
death_occurrence_range = [2, 4]  # todo: GET REAL DATA FOR THIS
asymptomatic_prob = 0.33  # REF 1 (0.35)
# The prob of death GIVEN severe symptoms (by age in the same way as severity by age)
# Since dying is a subset of severe (only people who had severe symptoms died) then its just fatality (given by REF 8)
# divided by severity by age (which I made up but is still based off of REF 8)
case_fatality_rate_by_age_given_severe_symptoms = [(10, 0.04), (20, 0.02), (40, 0.02), (50, 0.065), (60, 0.2), (70, 0.37)]

death_prob = 0.25

# todo: add a testing policy!!!!!
policies_safety = {
    'high': {'social_distance_prob': 0.75, 'wear_mask_prob': 0.75, 'low_movement_prob': 0.75},
    'medium': {'social_distance_prob': 0.5, 'wear_mask_prob': 0.5, 'low_movement_prob': 0.5},
    'low': {'social_distance_prob': 0.25, 'wear_mask_prob': 0.25, 'low_movement_prob': 0.25},
}
policy_type = 'low'

class CellularAutomation:
    def __init__(self, data_collect):
        self.data_collect = data_collect
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
        corrected_x = corrected(x, grid_width)
        corrected_y = corrected(y, grid_height)
        return corrected_x, corrected_y

    def _is_empty(self, x=None, y=None, position=None):
        if x and y:
            return self.grid[y, x] is None
        return self.grid[position[1], position[0]] is None

    def _kill_person(self, id, social_distance):
        person = self.id_person[id]
        if social_distance: self.ids_social_distance.remove(id)
        else: self.ids_not_social_distance.remove(id)
        position = person.position
        self._clear_cell(position)
        assert person.infected
        self.data_collect.increment_death_data()
        self.data_collect.add_lifetime_infected(person.num_people_infected)
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

        if not infected: self.data_collect.increment_initial_S()

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
        data_collect.update_data(person)
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
            abs_x = x + rel_x
            abs_y = y + rel_y
            correct_x, correct_y = self._get_cell_pos(abs_x, abs_y)
            located_id = self.grid[correct_y, correct_x]  # Might be None if no person there
            if located_id == None:
                yield None, (correct_x, correct_y), (rel_x, rel_y)
            else:
                yield self.id_person[located_id], (correct_x, correct_y), (rel_x, rel_y)

    # This decides movement and num of infected neighbors FOR SD people
    def _check_neighbors_SD(self, id, person):
        def check_neighbors(last_position=None):
            safe_cells = {(-1, -1): None, (0, -1): None, (1, -1): None, (-1, 0): None, (1, 0): None, (-1, 1): None, (0, 1): None, (1, 1): None}
            infected_neighbors = []
            for neighbor, neighbor_pos, neighbor_pos_rel in self._yield_neighbors(person.position, 3):
                if neighbor_pos == person.position:
                    continue
                # Get abs pos
                safe_cells[neighbor_pos_rel] = neighbor_pos
                # Add to infected if infectious neighbor
                if neighbor and neighbor.is_infectious():
                    infected_neighbors.append(neighbor)
                # Remove from safe cell if cell contains a person or it was the last pos
                if neighbor or last_position == neighbor_pos:
                    del safe_cells[neighbor_pos_rel]
            return infected_neighbors, safe_cells
        # First get number of infected around this and check if it gets infected
        infected_neighbors, safe_cells = check_neighbors()
        # Check if infected
        self._check_infection(person, infected_neighbors)
        # Then Moving
        # Move it if its own cell is not safe OR its moving intenionally
        if len(safe_cells) < 8 or np.random.random() < person.movement_prob:
            for m in range(move_length):
                last_position = person.position
                did_move = False
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
                    # First one that is safe: move there
                    if safe:
                        self._move_person(id, person, safe_cell_abs_pos)
                        infected_neighbors, safe_cells = check_neighbors(last_position)
                        self._check_infection(person, infected_neighbors)
                        did_move = True
                        break
                # End if it did not move
                if not did_move:
                    break

    # If not SD then move if moving intentionally
    def _check_neighbors_not_SD(self, id, person):
        def check_neighbors(last_position=None):
            empty_spots = []
            infected_neighbors = []
            for neighbor, neighbor_pos, _ in self._yield_neighbors(person.position, 3):
                if neighbor_pos == person.position:
                    continue
                # Add to infected if infectious neighbor
                if neighbor and neighbor.is_infectious():
                    infected_neighbors.append(neighbor)
                # Add empty spot (also if not the last position the person was at if moving more than once)
                if not neighbor and neighbor_pos != last_position:
                    empty_spots.append(neighbor_pos)
            return infected_neighbors, empty_spots
        # First get number of infected around this and check if it gets infected
        infected_neighbors, empty_spots = check_neighbors()
        # Check if infected
        self._check_infection(person, infected_neighbors)
        # Then Moving
        if np.random.random() < person.movement_prob:
            for m in range(move_length):
                # if somewhere to move
                if len(empty_spots) > 0:
                    new_spot = random.choice(empty_spots)
                    last_position = person.position
                    self._move_person(id, person, new_spot)
                    infected_neighbors, empty_spots = check_neighbors(last_position)
                    self._check_infection(person, infected_neighbors)
                else:
                    break

    def _check_infection(self, person, infected_neighbors):
        newly_infected = person.gets_infected(len(infected_neighbors), base_infection_prob, mask_infection_prob_decrease,
                                              self.data_collect)
        # If this person was just infected then add to the num of people infected to each neighbor for calc. Ro
        if newly_infected:
            for person in infected_neighbors:
                person.num_people_infected += 1

    def _update_person(self, id):
        person = self.id_person[id]
        # Progress Infection (if infected)
        dead, new_SD = person.progress_infection(self.data_collect)
        if dead:
            self._kill_person(id, person.social_distance)
            return None # Continue to next person
        # At the start figure out where the person is going to move AND the number of infected persons around them
        self._check_neighbors_SD(id, person) if person.social_distance else self._check_neighbors_not_SD(id, person)
        return new_SD

    # For rendering
    def _get_person_color(self, person):
        if current_color_model == 'SIR':
            colors = color_models['SIR']
            if person.susceptible: return colors['susceptible']
            if person.infected: return colors['infected']
            return colors['recovered']

    def run(self, render=False):
        if render:
            # Initialize the game engine
            pygame.init()
            # Set the height and width and title of the screen
            screen = pygame.display.set_mode((screen_width, screen_height))
            pygame.display.set_caption("Population Dynamics")
            clock = pygame.time.Clock()
            # Initially set the screen to all black
            screen.fill((0, 0, 0))
        for t in range(number_iterations):
            self.data_collect.reset(t)
            def loop_through_ids(ids):
                # Keep track of any switches between SD lists
                new_SD_list = []
                new_not_SD_list = []
                # Shuffle - Random order
                lis = list(ids)
                random.shuffle(lis)
                for id in lis:
                    new_SD = self._update_person(id)
                    # If dead then continue
                    if id not in self.id_person: continue
                    if new_SD is True: new_SD_list.append(id)
                    elif new_SD is False: new_not_SD_list.append(id)
                    # Update data collection
                    self.data_collect.update_data(self.id_person[id])
                    # Render if not dead
                    if render:
                        person = self.id_person[id]
                        pygame.draw.rect(screen, self._get_person_color(person),
                                         [person.position[0] * cell_size, person.position[1] * cell_size, cell_size, cell_size])
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
            if render:
                pygame.display.flip()
                screen.fill((0, 0, 0))
                # Frames per second
                if fps: clock.tick(fps)
        self.data_collect.reset(t+1, last=True)

data_collect = DataCollector()
data_collect.set_print_options(basic_to_print=['S', 'I', 'R', 'death'])
CA = CellularAutomation(data_collect)
CA.run(render=False)
