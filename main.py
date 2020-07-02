import numpy as np
import random
from person import Person

np.random.seed(42)

# Grid
grid_width = 100
grid_height = 100
initial_pop_size = 200
neighborhood_side_length = 5  # So social distancing can be done
number_iterations = 100

# Person Initial Attributes
age_range = [5, 80]  # Range
movement_prob = {'low': 0.25, 'high': 0.75}  # Choices (prob. of moving that step)

policies_safety = {
    'high': {'social_distance_prob': 0.75, 'wear_mask_prob': 0.75, 'low_movement_prob': 0.75},
    'medium': {'social_distance_prob': 0.5, 'wear_mask_prob': 0.5, 'low_movement_prob': 0.5},
    'low': {'social_distance_prob': 0.25, 'wear_mask_prob': 0.25, 'low_movement_prob': 0.25},
}
policy_type = 'medium'

# Virus/Disease Attributes (COVID-19)


class CellularAutomation:
    def __init__(self):
        # Need two lists of ids (correspond uniquely to a person)
        # 1) Those who practice social distancing
        # 2) Those who do not practice social distancing
        self.ids_social_distance = []
        self.ids_not_social_distance = []
        # The person objects
        # id (int): person (object)
        self.id_person = {}
        # The peoples' positions
        # id (int): pos (int, int)
        self.id_pos = {}
        # Each positions precalculated neighbor positions (based on range)
        # pos (int, int): list of pos [(int, int),...]
        self.pos_neighbors = self._create_neighbor_pos_dict()
        self.grid = np.empty(shape=(grid_height, grid_width), dtype=np.object)
        self.next_id = 0
        # The currently open positions (no person on it)
        self.open_positions = []
        for y in range(grid_height):
            for x in range(grid_width):
                self.open_positions.append((x, y))
        # Initialize the grid
        self._initialize_grid()

    # Create dict of pos to each of its neighbor positions
    def _create_neighbor_pos_dict(self):
        dic = {}
        for y in range(grid_height):
            for x in range(grid_width):
                neighbors = []
                for i in range(neighborhood_side_length ** 2):
                    cluster_mid = neighborhood_side_length // 2
                    rel_x = (i % neighborhood_side_length) - cluster_mid
                    rel_y = (i // neighborhood_side_length) - cluster_mid
                    abs_x = x + rel_x
                    abs_y = y + rel_y
                    correct_x, correct_y = self._get_cell_pos(abs_x, abs_y)
                    neighbors.append((correct_x, correct_y))
                dic[(x, y)] = neighbors
        return dic

    # Out of bounds
    def _oob(self, x, y):
        return x < 0 or y < 0 or x >= grid_width or y >= grid_height

    # Env wraps so get correct pos
    def _get_cell_pos(self, x, y):
        def corrected(val, max_val):
            if val < 0:
                 return max_val + val
            elif val > max_val:
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
        position = self.id_pos[id]
        self._clear_cell(position)
        del self.id_person[id]
        del self.id_pos[id]

    def _clear_cell(self, position):
        self.grid[position[1], position[0]] = None
        self.open_positions.append(position)

    def _add_to_cell(self, id, position):
        assert self._is_empty(position=position)
        self.id_pos[id] = position
        self.grid[position[1], position[0]] = id
        self.open_positions.remove(position)

    def _move_person(self, id, new_position):
        # assert self._is_empty(position=new_position)
        current_position = self.id_pos[id]
        # Clear current position
        self._clear_cell(current_position)
        # Place person in new cell
        self._add_to_cell(id, new_position)

    # Grid initialization ------
    def _create_person(self, position):
        assert self._is_empty(position=position)
        age = np.random.randint(age_range[0], age_range[1]+1)
        policy = policies_safety[policy_type]
        SD_prob = policy['social_distance_prob']
        SD = True if np.random.random() <= SD_prob else False
        WM_prob = policy['wear_mask_prob']
        WM = True if np.random.random() <= WM_prob else False
        LM_prob = policy['low_movement_prob']
        LM = movement_prob['low'] if np.random.random() <= LM_prob else movement_prob['high']
        person = Person(age, SD, WM, LM)
        self.id_person[self.next_id] = person
        if SD: self.ids_social_distance.append(self.next_id)
        else: self.ids_not_social_distance.append(self.next_id)
        self._add_to_cell(self.next_id, position)
        self.next_id += 1

    # Create all the people
    def _initialize_grid(self):
        for p in range(initial_pop_size):
            # Select random position
            position = np.random.choice(self.open_positions)
            # Create person
            self._create_person(position)

    def _update_person(self, id):
        ...

    def run(self):
        for t in range(number_iterations):
            def loop_through_ids(ids):
                # Shuffle - Random order
                for id in random.sample(ids, len(ids)):
                    self._update_person(id)
            # Update (in random order) those who do NOT practice social distancing
            loop_through_ids(self.ids_not_social_distance)
            # Next update (in random order) those who DO practice social distancing, so they get to be at a safe dist.
            # from others at the end of the iteration
            loop_through_ids(self.ids_social_distance)
