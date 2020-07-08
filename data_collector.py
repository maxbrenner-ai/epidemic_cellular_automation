from collections import defaultdict


data_options = ['S', 'I', 'R', 'WM', 'SD', 'death', 'mild', 'severe', 'asymptomatic']
advanced_equations = ['SAR', 'Ro', 'RoS']

class DataCollector:
    def __init__(self):
        self.current_data = defaultdict(int)
        self.data_history = defaultdict(list)
        self.to_print = None
        self.frequency_print = 1

        # For adv equations
        # For SAR (Secondary Attack Rate) need total number of infected overtime
        self.total_infected = 0
        # And need number of S not including initial infected
        self.initial_S = 0

    def set_print_options(self, to_print='all', frequency=1):
        self.to_print = data_options if to_print == 'all' else to_print
        self.frequency_print = frequency

    def increment_total_infected(self):
        self.total_infected += 1

    def increment_initial_S(self):
        self.initial_S += 1

    def update_data(self, person):
        self.current_data['S'] += person.susceptible
        self.current_data['I'] += person.infected
        self.current_data['R'] += person.recovered
        self.current_data['WM'] += person.wear_mask
        self.current_data['SD'] += person.social_distance
        if person.current_symptom_stage == 'mild':
            self.current_data['mild'] += 1
        elif person.current_symptom_stage == 'severe':
            self.current_data['severe'] += 1
        elif person.current_symptom_stage == 'asymptomatic':
            self.current_data['asymptomatic'] += 1

    def increment_death_data(self):
        self.current_data['death'] += 1

    def reset(self, timestep, last=False):
        # Aggregate history data
        for key, val in list(self.current_data.items()):
            self.data_history[key].append(val)
        # Print
        if timestep % self.frequency_print == 0 and self.to_print and len(self.to_print) > 0:
            st = 'At timestep: {} --- '.format(timestep)
            for i, val in enumerate(self.to_print):
                st += '{}: {}'.format(val, self.current_data[val])
                if i != len(self.to_print)-1:
                    st += ' --- '
            print(st)
        # Reset data
        for k in list(self.current_data.keys()):
            self.current_data[k] = 0
        # If last print advanced equations
        if last:
            print('Secondary Attack Rate (SAR): {} / {} = {:.02f}'.format(self.total_infected, self.initial_S,
                                                                     self.total_infected / self.initial_S))