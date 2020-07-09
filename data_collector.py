from collections import defaultdict


data_options = ['S', 'I', 'R', 'WM', 'SD', 'death', 'mild', 'severe', 'asymptomatic']
advanced_equations = ['SAR', 'R0', 'R0S']

class DataCollector:
    def __init__(self):
        self.current_data = defaultdict(int)
        self.data_history = defaultdict(list)
        self.basic_to_print = None
        self.adv_to_print = None
        self.frequency_print = 1

        # For adv equations
        # For SAR (Secondary Attack Rate) need total number of infected overtime
        self.total_infected = 0
        # And need number of S not including initial infected
        self.initial_S = 0
        # For R0 need the current number of each infection lifetime for the current bin
        self.lifetime_infected_bin_size = 5
        self.current_bin_lifetime_infected = []
        # Saves all the bin averages
        self.lifetime_infected_bin_avgs = {}
        self.last_bin_avg = None

    def set_print_options(self, basic_to_print='all', adv_to_print='all', frequency=1):
        self.basic_to_print = data_options if basic_to_print == 'all' else basic_to_print
        self.adv_to_print = advanced_equations if adv_to_print == 'all' else adv_to_print
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

    def add_lifetime_infected(self, num):
        self.current_bin_lifetime_infected.append(num)

    def reset(self, timestep, last=False):
        # Aggregate history data
        for key, val in list(self.current_data.items()):
            self.data_history[key].append(val)
        # If bin is done in lifetime infected get avg and empty bin
        bin_avg = None
        if timestep % self.lifetime_infected_bin_size == 0 and timestep != 0:
            # Have it be the last bin avg if no people recorded (if no val yet then return None)
            if len(self.current_bin_lifetime_infected) == 0:
                bin_avg = self.last_bin_avg
            else:
                bin_avg = sum(self.current_bin_lifetime_infected) / len(self.current_bin_lifetime_infected)
            self.last_bin_avg = bin_avg
            self.lifetime_infected_bin_avgs[timestep] = bin_avg
            self.current_bin_lifetime_infected = []
        # Print
        if timestep % self.frequency_print == 0 and (self.basic_to_print or self.adv_to_print):
            st = 'At timestep: {} --- '.format(timestep)
            if self.basic_to_print:
                for i, val in enumerate(self.basic_to_print):
                    st += '{}: {}'.format(val, self.current_data[val])
                    if i != len(self.basic_to_print)-1:
                        st += ' --- '
            if self.adv_to_print:
                if 'R0' in self.adv_to_print and bin_avg != None:
                    st += '\nBasic Reproduction Number (R0): {:.02f}'.format(bin_avg)
                if 'R0S' in self.adv_to_print and bin_avg != None:
                    st += '\nR0S: {:.02f} x {} = {:.02f}'.format(bin_avg, self.current_data['S'], bin_avg * self.current_data['S'])
            print(st)
        # Reset data
        for k in list(self.current_data.keys()):
            self.current_data[k] = 0
        # If last print advanced equations
        if last:
            if 'SAR' in self.adv_to_print:
                print('Secondary Attack Rate (SAR): {} / {} = {:.02f}'.format(self.total_infected, self.initial_S,
                                                                       self.total_infected / self.initial_S))