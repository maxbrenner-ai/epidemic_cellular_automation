from collections import OrderedDict
import matplotlib.pyplot as plt
import os
from datetime import datetime
import json
import pandas as pd


data_options = ['S', 'I', 'R', 'WM', 'SD', 'death', 'mild', 'severe', 'asymptomatic']

# SAR -> Secondary Attack Rate = total # infected people / total # susceptible (overall metric, ie calculated at end)
# R0 -> Basic Reproductive Number = The number of people an infected person directly infects
# R0S -> R0 x S -> If > 1 then can multiply, = 1 then can become endemic (persistent but tame), < 1 then can die off
advanced_equations = ['SAR', 'R0', 'R0S']

# Plot figure size. Width, height in inches??
size = (16, 10)
# Background color. Possible color: https://matplotlib.org/stable/gallery/color/named_colors.html
plt.rcParams['figure.facecolor'] = 'silver'
plt.rcParams['savefig.facecolor'] = 'silver'
# Frame color
plt.rcParams['axes.facecolor'] = 'lightgrey'
# Draw frame or not
plot_frame = True
# Tight layout
tight = True


class DataCollector:
    def __init__(self, constants, save_experiment, print_visualizations):
        self.current_deaths = []
        self.current_infected = 0
        self.percent_deaths = 0.0
        self.percent_rec = 0.0
        self.current_deaths_percent = []
        self.current_recovered_percent = []
        self.current_infected_percent = []
        self.total_deaths = 0
        self.total_recovered = 0
        self.population = 0
        self.constants = constants
        self.save_experiment = save_experiment
        self.print_visualizations = print_visualizations
        self.basic_to_print = None
        self.adv_to_print = None
        self.frequency_print = 1
        self._reset_data_options(hist=True)
        # Advanced Infection data collection
        # WM, SD, both, neither, total
        self.adv_infection_data = {'total': 0, 'SD': 0, 'not SD': 0, 'R': 0}
        self.adv_infection_data_history = OrderedDict({'total': [], 'SD': [], 'not SD': [], 'R': []})
        # For adv equations
        # For SAR (Secondary Attack Rate) need total number of infected overtime
        self.total_infected = 0
        # And need number of S not including initial infected
        self.initial_S = 0
        # For R0 need the current number of each infection lifetime for the current bin
        self.lifetime_infected_bin_size = 5
        self.current_bin_lifetime_infected = []
        # Saves all the bin averages
        self.lifetime_infected_bin_avgs = OrderedDict()
        self.last_bin_avgs = {'total': None, 'SD': None, 'not SD': None, 'WM': None, 'not WM': None, 'both': None, 'neither': None}

    def _reset_data_options(self, hist=False):
        self.current_data = {}
        if hist: self.data_history = OrderedDict()
        for k in data_options:
            self.current_data[k] = 0
            if hist: self.data_history[k] = []

    def set_print_options(self, basic_to_print='all', adv_to_print='all', frequency=1):
        self.basic_to_print = data_options if basic_to_print == 'all' else basic_to_print
        self.adv_to_print = advanced_equations if adv_to_print == 'all' else adv_to_print
        self.frequency_print = frequency

    def increment_total_infected(self):
        self.total_infected += 1

    def increment_initial_S(self):
        self.initial_S += 1

    def _update_adv_infection_data(self, person):
        SD = person.social_distance
        not_SD = not SD
        self.adv_infection_data['total'] += 1
        if SD: self.adv_infection_data['SD'] += 1
        if not_SD: self.adv_infection_data['not SD'] += 1

    def _update_adv_infection_data_rec(self, person):
        R = person.recovered
        if R: self.adv_infection_data['R'] += 1

    def update_data(self, person):
        self.current_data['S'] += person.susceptible
        self.current_data['I'] += person.infected
        if person.infected:
            self._update_adv_infection_data(person)
        if person.recovered:
            self._update_adv_infection_data_rec(person)
        self.current_data['R'] += person.recovered
        self.current_data['WM'] += person.wear_mask
        self.current_data['SD'] += person.social_distance
        if person.current_symptom_stage == 'mild':
            self.current_data['mild'] += 1
        elif person.current_symptom_stage == 'severe':
            self.current_data['severe'] += 1
        elif person.current_symptom_stage == 'asymptomatic':
            self.current_data['asymptomatic'] += 1

    def increment_death_data(self, person):
        self.current_data['death'] += 1

    def add_lifetime_infected(self, num_infected, infectious_days_info):
        # Bin infectious_days_info into majority SD, minority SD, majority WM, minority WM (ie did they SD more often then not)
        SD = infectious_days_info['SD'] > infectious_days_info['not SD']
        WM = infectious_days_info['WM'] > infectious_days_info['not WM']
        both = SD and WM
        neither = not SD and not WM
        self.current_bin_lifetime_infected.append({'total': num_infected, 'SD': SD, 'not SD': not SD, 'WM': WM,
                                                   'not WM': not WM, 'both': both, 'neither': neither})

    def reset(self, timestep, last=False):
        # Aggregate history data
        for key, value in list(self.current_data.items()):
            self.data_history[key].append(value)
        for key, value in list(self.adv_infection_data.items()):
            self.adv_infection_data_history[key].append(value)
            self.adv_infection_data[key] = 0
        # If bin is done in lifetime infected get avg and empty bin
        if timestep % self.lifetime_infected_bin_size == 0 and timestep != 0:
            self.lifetime_infected_bin_avgs[timestep] = {}
            # If no one infected recovered/died then move on
            if len(self.current_bin_lifetime_infected) == 0:
                # Set to the last avgs initially and if new ones then set them
                for k, last_avg in list(self.last_bin_avgs.items()):
                    self.lifetime_infected_bin_avgs[timestep][k] = last_avg
            else:
                for k in list(self.last_bin_avgs.keys()):
                    bin_arr = [dic['total'] for dic in self.current_bin_lifetime_infected if dic[k]]
                    if len(bin_arr) == 0:  # No people with that bin type
                        self.lifetime_infected_bin_avgs[timestep][k] = self.last_bin_avgs[k]
                        continue
                    bin_avg = sum(bin_arr) / len(bin_arr)
                    self.lifetime_infected_bin_avgs[timestep][k] = bin_avg
                    self.last_bin_avgs[k] = bin_avg
            self.current_bin_lifetime_infected = []
        # Print if frequency > 0
        if self.frequency_print > 0:
            if timestep % self.frequency_print == 0 and (self.basic_to_print or self.adv_to_print):
                st = 'At timestep: {} --- '.format(timestep)
                if self.basic_to_print:
                    for i, val in enumerate(self.basic_to_print):
                        st += '{}: {}'.format(val, self.current_data[val])
                        if i != len(self.basic_to_print) - 1:
                            st += ' --- '
                if self.adv_to_print:
                    if timestep in self.lifetime_infected_bin_avgs:
                        total_bin_avg = self.lifetime_infected_bin_avgs[timestep]['total']
                        if 'R0' in self.adv_to_print and total_bin_avg is not None:
                            st += '\nBasic Reproduction Number (R0): {:.02f}'.format(total_bin_avg)
                        if 'R0S' in self.adv_to_print and total_bin_avg is not None:
                            st += '\nR0S: {:.02f} x {} = {:.02f}'.format(total_bin_avg, self.current_data['S'], total_bin_avg * self.current_data['S'])
                print(st)
        # Save some stats for "if last is True"
        self.total_deaths += self.current_data['death']
        self.current_deaths.append(self.total_deaths)
        self.total_recovered = self.current_data['R']  # current_data 'R' is always current total
        self.current_infected = self.current_data['I']  # for check if no infected then stop calculation in 173
        # Reset data
        self._reset_data_options()
        # If last print advanced equations
        if last or self.current_infected == 0:
            SAR = self.total_infected / self.initial_S
            if 'SAR' in self.adv_to_print:
                print('Secondary Attack Rate (SAR): {} / {} = {:.02f}'.format(self.total_infected, self.initial_S, SAR))
            # Convert the lifetime infected bin avgs to a a dict of lists and a list for the x-vals
            self.R0_hist = {'total': [], 'SD': [], 'WM': [], 'not SD': [], 'not WM': [], 'both': [], 'neither': []}
            self.R0S_hist = {'total': [], 'SD': [], 'WM': [], 'not SD': [], 'not WM': [], 'both': [], 'neither': []}
            self.R0_xvals = []
            for x_val, info in list(self.lifetime_infected_bin_avgs.items()):
                self.R0_xvals.append(x_val)
                S = self.data_history['S'][x_val]
                for k, y_val in list(info.items()):
                    if not y_val: y_val = 0.0  # Why use 'np.nan'? It produces ugly spaces in the line graph and is the only reason for numpy import
                    R0 = y_val
                    R0S = S * y_val
                    self.R0_hist[k].append(R0)
                    self.R0S_hist[k].append(R0S)

            # Visualizations
            fig, axs = plt.subplots(2, 2, figsize=size, frameon=plot_frame, tight_layout=tight)
            # Infections
            I_xvals = list(range(len(self.adv_infection_data_history['total'])))
            axs[0, 0].plot(I_xvals, self.adv_infection_data_history['total'], 'C0', label='total')
            axs[0, 0].plot(I_xvals, self.adv_infection_data_history['SD'], 'C2', label='SD')
            axs[0, 0].plot(I_xvals, self.adv_infection_data_history['not SD'], 'C3', label='not SD')
            axs[0, 0].set_ylabel('# people')
            axs[0, 0].set_title('Infections at time step based on SD')
            axs[0, 0].legend(loc="upper left")

            # percent of once infected - of population. Also mentions deaths, but doesn't calc with
            self.population = self.constants['grid'].get('initial_pop_size')
            for value in self.adv_infection_data_history['R']:
                self.current_recovered_percent.append((100.0 / self.population) * value)
            for value in self.adv_infection_data_history['total']:
                self.current_infected_percent.append((100.0 / self.population) * value)
            for value in self.current_deaths:
                self.current_deaths_percent.append((100.0 / self.population) * value)
            self.percent_rec = (100.0 / self.population) * self.total_recovered
            self.percent_deaths = (100.0 / self.population) * self.total_deaths
            axs[0, 1].plot(I_xvals, self.current_recovered_percent, label='Percent had virus and recovered (%1.3f %%, %i final)' % (self.percent_rec, self.total_recovered))
            axs[0, 1].plot(I_xvals, self.current_infected_percent, label='Percent infected at time step')
            axs[0, 1].plot(I_xvals, self.current_deaths_percent, 'C3', label='Percent had virus and died (%1.3f %% final)' % self.percent_deaths)
            axs[0, 1].set_ylabel('percent')
            axs[0, 1].set_title('Percentages of initial population of %i. Total deaths = %i ' % (self.population, self.total_deaths))
            axs[0, 1].legend(loc="upper left")

            # R0
            R0_xvals = self.R0_xvals
            axs[1, 0].plot(R0_xvals, self.R0_hist['total'], 'C0', label='total')
            axs[1, 0].plot(R0_xvals, self.R0_hist['SD'], 'C2', label='SD')
            axs[1, 0].plot(R0_xvals, self.R0_hist['not SD'], 'C3', label='not SD')
            axs[1, 0].plot(R0_xvals, self.R0_hist['WM'], 'C4', label='WM')
            axs[1, 0].plot(R0_xvals, self.R0_hist['not WM'], 'C1', label='not WM')
            axs[1, 0].plot(R0_xvals, self.R0_hist['both'], 'C5', label='both')
            axs[1, 0].plot(R0_xvals, self.R0_hist['neither'], 'C6', label='neither')
            axs[1, 0].set_ylabel('R0')
            axs[1, 0].set_xlabel('time step')
            axs[1, 0].set_title('R0 based on SD and WM')
            axs[1, 0].legend(loc="upper left")

            # R0S
            axs[1, 1].plot(R0_xvals, self.R0S_hist['total'], 'C0', label='total')
            axs[1, 1].plot(R0_xvals, self.R0S_hist['SD'], 'C2', label='SD')
            axs[1, 1].plot(R0_xvals, self.R0S_hist['not SD'], 'C3', label='not SD')
            axs[1, 1].plot(R0_xvals, self.R0S_hist['WM'], 'C4', label='WM')
            axs[1, 1].plot(R0_xvals, self.R0S_hist['not WM'], 'C1', label='not WM')
            axs[1, 1].plot(R0_xvals, self.R0S_hist['both'], 'C5', label='both')
            axs[1, 1].plot(R0_xvals, self.R0S_hist['neither'], 'C6', label='neither')
            axs[1, 1].set_ylabel('R0S')
            axs[1, 1].set_xlabel('time step')
            axs[1, 1].set_title('R0S based on SD and WM')
            axs[1, 1].legend(loc="upper left")

            # Save
            if self.save_experiment:
                # Create new directory (name of current date and time)
                now = datetime.now()
                dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
                sub_dir = os.path.join('experiments', dt_string)
                new_dir = os.path.join(os.getcwd(), sub_dir)
                os.mkdir(new_dir)
                # Save constants
                constants_file = os.path.join(sub_dir, 'constants.json')
                json.dump(self.constants, open(constants_file, 'w'), indent=4)
                # Save visualizations
                figure_file = os.path.join(sub_dir, 'plots.png')
                plt.savefig(figure_file)  # transparent=True
                # Save data as .csv and txt
                # Basic
                basic_data_file = os.path.join(sub_dir, 'basic_data.csv')
                self.data_history['timestep'] = I_xvals
                basic_data_df = pd.DataFrame(data=self.data_history)
                basic_data_df.to_csv(basic_data_file, index=False)
                # Advanced infection
                adv_I_file = os.path.join(sub_dir, 'infection_data.csv')
                self.adv_infection_data_history['timestep'] = I_xvals
                adv_I_df = pd.DataFrame(data=self.adv_infection_data_history)
                adv_I_df.to_csv(adv_I_file, index=False)
                # R0
                R0_file = os.path.join(sub_dir, 'R0_data.csv')
                self.R0_hist['timestep'] = self.R0_xvals
                R0_df = pd.DataFrame(data=self.R0_hist)
                R0_df.to_csv(R0_file, index=False)
                # R0S
                R0S_file = os.path.join(sub_dir, 'R0S_data.csv')
                self.R0S_hist['timestep'] = self.R0_xvals
                R0S_df = pd.DataFrame(data=self.R0S_hist)
                R0S_df.to_csv(R0S_file, index=False)
                # Save SAR to txt file
                SAR_file = os.path.join(sub_dir, 'SAR.txt')
                with open(SAR_file, 'w') as f:
                    f.write(str(SAR))

            if self.print_visualizations:
                plt.show()

            quit()  # Because it would throw unessecary error due to "or self.current_infected is 0" (line 173), and I just couldn't figure out why it's being run again after first "last=True"
