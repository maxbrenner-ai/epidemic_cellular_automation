

data_options = ['S', 'I', 'R', 'WM', 'SD', 'death', 'mild', 'severe', 'asymptomatic']
advanced_equations = ['SAR', 'R0', 'R0S']

class DataCollector:
    def __init__(self):
        self.basic_to_print = None
        self.adv_to_print = None
        self.frequency_print = 1
        self._reset_data_options(hist=True)
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
        self.last_bin_avgs = {'total': None, 'SD': None, 'not SD': None, 'WM': None, 'not WM': None}

    def _reset_data_options(self, hist=False):
        self.current_data = {}
        if hist: self.data_history = {}
        for k in data_options:
            self.current_data[k] = {'total': 0, 'SD': 0, 'WM': 0, 'both': 0, 'neither': 0}
            if hist: self.data_history[k] = {'total': [], 'SD': [], 'WM': [], 'both': [], 'neither': []}

    def set_print_options(self, basic_to_print='all', adv_to_print='all', frequency=1):
        self.basic_to_print = data_options if basic_to_print == 'all' else basic_to_print
        self.adv_to_print = advanced_equations if adv_to_print == 'all' else adv_to_print
        self.frequency_print = frequency

    def increment_total_infected(self):
        self.total_infected += 1

    def increment_initial_S(self):
        self.initial_S += 1

    def _update_data_slot(self, val, person, sym=False):
        if sym and person.current_symptom_stage != val:
            return
        SD = person.social_distance
        WM = person.wear_mask
        both = SD and WM
        neither = not both
        dict = self.current_data[val]
        if SD: dict['SD'] += 1
        if WM: dict['WM'] += 1
        if both: dict['both'] += 1
        if neither: dict['neither'] += 1

    def update_data(self, person):
        for k in data_options:
            if k == 'death': continue
            self._update_data_slot(k, person, sym=k in ['mild', 'severe', 'asymptomatic'])

    def increment_death_data(self, person):
        self._update_data_slot('death', person)

    def add_lifetime_infected(self, num_infected, infectious_days_info):
        # Bin infectious_days_info into majority SD, minority SD, majority WM, minority WM (ie did they SD more often then not)
        SD = infectious_days_info['SD'] > infectious_days_info['not SD']
        WM = infectious_days_info['WM'] > infectious_days_info['not WM']
        self.current_bin_lifetime_infected.append({'infected': num_infected, 'SD': SD, 'not SD': not SD, 'WM': WM, 'not WM': not WM})

    def reset(self, timestep, last=False):
        # Aggregate history data
        for key, dic in list(self.current_data.items()):
            for k, v in list(dic.items()):
                self.data_history[key][k].append(v)
        # If bin is done in lifetime infected get avg and empty bin
        bin_avg = None
        if timestep % self.lifetime_infected_bin_size == 0 and timestep != 0:
            self.lifetime_infected_bin_avgs[timestep] = {}
            # If no one infected recovered/died them move on
            if len(self.current_bin_lifetime_infected) == 0:
                # Set to the last avgs initially and if new ones then set them
                for k, last_avg in list(self.last_bin_avgs.items()):
                    self.lifetime_infected_bin_avgs[timestep][k] = last_avg
            else:
                for k in list(self.last_bin_avgs.keys()):
                    bin_arr = [dic['infected'] for dic in self.current_bin_lifetime_infected if k != 'total' and dic[k]]
                    if len(bin_arr) == 0:  # No people with that bin type
                        self.lifetime_infected_bin_avgs[timestep][k] = self.last_bin_avgs[k]
                        continue
                    bin_avg = sum(bin_arr) / len(bin_arr)
                    self.lifetime_infected_bin_avgs[timestep][k] = bin_avg
                    self.last_bin_avgs[k] = bin_avg
            self.current_bin_lifetime_infected = []
        # Print
        if timestep % self.frequency_print == 0 and (self.basic_to_print or self.adv_to_print):
            st = 'At timestep: {} --- '.format(timestep)
            if self.basic_to_print:
                for i, val in enumerate(self.basic_to_print):
                    st += '{}: {}'.format(val, self.current_data[val]['total'])
                    if i != len(self.basic_to_print)-1:
                        st += ' --- '
            if self.adv_to_print:
                if 'R0' in self.adv_to_print and bin_avg != None:
                    st += '\nBasic Reproduction Number (R0): {:.02f}'.format(bin_avg)
                if 'R0S' in self.adv_to_print and bin_avg != None:
                    st += '\nR0S: {:.02f} x {} = {:.02f}'.format(bin_avg, self.current_data['S']['total'], bin_avg * self.current_data['S']['total'])
            print(st)
        # Reset data
        self._reset_data_options()
        # If last print advanced equations
        if last:
            if 'SAR' in self.adv_to_print:
                print('Secondary Attack Rate (SAR): {} / {} = {:.02f}'.format(self.total_infected, self.initial_S,
                                                                       self.total_infected / self.initial_S))