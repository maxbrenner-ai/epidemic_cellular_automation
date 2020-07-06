import numpy as np

'''
Notes:
- There are separate probs for wearing a mask and social distancing, meaning some people will do both, one or the other
  or neither
- There is an altruistic prob, where people who get mild symptoms have a chance of wearing a mask and social
  distancing (for as long as their symptoms last) if they weren't before.
    - It also says whether someone will intentionally move at a low rate
- People who experience severe symptoms will automatically wear masks and social distance and no longer intentionally move
  but just move defensively
'''
class Person:
    def __init__(self, position, age, social_distance, wear_mask, movement_prob, low_movement_prob, altruistic_prob, infected,
                 total_length_infection, incubation_period_duration_range, infectious_start_before_symptoms_range,
                 infectious_period_duration_range, severe_symptoms_start_range, fatality_occur_range,
                 asymptomatic_prob, severe_prob, fatality_prob):
        self.position = self.set_position(position)
        self.age = age
        self.social_distance = social_distance
        self.social_distance_before_symptoms = social_distance
        self.wear_mask = wear_mask
        self.wear_mask_before_symptoms = wear_mask
        self.movement_prob = movement_prob
        self.low_movement_prob = low_movement_prob
        self.movement_prob_before_symptoms = movement_prob
        self.altruistic = np.random.random() < altruistic_prob

        # Anyone with severe symptoms goes to hospital
        # self.hospitalized = False
        # Anyone with mild symptoms self-isolates
        # so this is probably a little more altruistic than normal unfortunately
        # self.self_isolating = False

        self.susceptible = not infected
        self.infected = infected
        # Most literature says that prob. of reinfection is very low of nonexistent at least in a short period of time
        # But scientists are still not sure
        self.recovered = False
        self.infection_step = -1

        # CREATE INFECTION PERIODS -----
        incubation_period_duration = np.random.randint(incubation_period_duration_range[0],
                                                       incubation_period_duration_range[1] + 1)
        infectious_start_before_symptoms = np.random.randint(infectious_start_before_symptoms_range[0],
                                                             infectious_start_before_symptoms_range[1] + 1)
        infectious_period_duration = np.random.randint(infectious_period_duration_range[0],
                                                       infectious_period_duration_range[1] + 1)
        severe_symptoms_start = np.random.randint(severe_symptoms_start_range[0], severe_symptoms_start_range[1] + 1)
        fatality_occur = np.random.randint(fatality_occur_range[0], fatality_occur_range[1] + 1)

        # Create Infection periods
        infectious_period_start = incubation_period_duration - infectious_start_before_symptoms
        assert infectious_period_start >= 1, \
            '{} is wrong: infectious period start should be greater than 0 because latent period is at least one day'.format(
                infectious_period_start)
        removed_period_start = infectious_period_duration + infectious_period_start
        assert removed_period_start < total_length_infection, \
            '{} is wrong: removal should be less than the total length of infection'.format(removed_period_start)
        # total_length = total_length_infection if removed_period_start < total_length_infection else removed_period_start + 1
        total_length = total_length_infection
        self.infectious_periods = [('latent', 0),
                                   ('infectious', infectious_period_start),
                                   ('remove', removed_period_start),
                                   ('recover', total_length)]

        # Symptoms is more complicated
        self.symptoms_periods = [('incubation', 0)]
        symptoms_start = incubation_period_duration
        assert symptoms_start > infectious_period_start, \
            'Symptoms ({}) start during infectious stage (starts {})'.format(symptoms_start, infectious_period_start)
        assert symptoms_start < removed_period_start, \
            'Symptoms ({}) start during infectious stage (starts {})'.format(symptoms_start, infectious_period_start)
        # 1) Some people are asymptomatic (and have no mild or severe symptoms, and also cant die)
        if np.random.random() < asymptomatic_prob:
            self.symptoms_periods.append(('asymptomatic', symptoms_start))
        # 2) If they arent asymptomatic they start with mild
        else:
            self.symptoms_periods.append(('mild', symptoms_start))
            # 3) Can have severe (or not)
            if np.random.random() < severe_prob:
                severe_start_abs = severe_symptoms_start + symptoms_start
                assert severe_start_abs <= total_length, \
                    'severe symptoms should start ({}) before end of infection'.format(severe_start_abs)
                self.symptoms_periods.append(('severe', severe_start_abs))
                # 4) Can die (or not)
                if np.random.random() < fatality_prob:
                    fatality_start_abs = fatality_occur + severe_symptoms_start + symptoms_start
                    assert fatality_start_abs <= total_length, \
                        'fatality should occur ({}) before end of infection'.format(fatality_start_abs)
                    self.symptoms_periods.append(('death', fatality_start_abs))
        # 5) If didnt die then recover
        if self.symptoms_periods[-1][0] != 'death':
            self.symptoms_periods.append(('recover', total_length))
        # Make sure the symptoms periods is one of 4 diff combinations
        possible_permutations = [['incubation', 'asymptomatic', 'recover'],
                                 ['incubation', 'mild', 'recover'],
                                 ['incubation', 'mild', 'severe', 'death'],
                                 ['incubation', 'mild', 'severe', 'recover']]
        assert [item[0] for item in self.symptoms_periods] in possible_permutations, \
            '{} not a possible symptoms stages permutation'.format(possible_permutations)

        self.current_symptom_stage = None
        self.current_infection_stage = None

        # print('Age: {} -- SD: {} -- WM: {} -- Movement: {} -- Altruitsic: {}'.format(self.age, self.social_distance, self.wear_mask, self.movement_prob, self.altruistic))
        # print('Infectious periods: {}'.format(self.infectious_periods))
        # print('Symptoms periods: {}'.format(self.symptoms_periods))

    def set_position(self, position):
        self.position = position

    # Not just infected but infectious
    def is_infectious(self):
        return self.current_infection_stage == 'infectious'

    def progress_infection(self):
        if not self.infected:
            return False, None
        self.infection_step += 1
        new_infection_stage = False
        new_symptoms_stage = False
        # print('Infection step: {}'.format(self.infection_step))
        # print('infection phase: {}'.format(self.current_infection_stage))
        # print('symptoms phase: {}'.format(self.current_symptom_stage))
        # If gets to new stage then pop off first
        if self.infection_step == self.infectious_periods[0][1]:
            self.current_infection_stage = self.infectious_periods[0][0]
            self.infectious_periods.pop(0)
            new_infection_stage = True
            # print('infection: {}'.format(self.infectious_periods))

        if self.infection_step == self.symptoms_periods[0][1]:
            self.current_symptom_stage = self.symptoms_periods[0][0]
            self.symptoms_periods.pop(0)
            new_symptoms_stage = True
            # print('symptoms: {}'.format(self.symptoms_periods))

        # If dead then return true
        if self.current_symptom_stage == 'death':
            # print('DEATH')
            return True, None

        new_SD = None
        # If mild symptoms check altruistic prob to see what happens
        if self.current_symptom_stage == 'mild' and self.altruistic and new_symptoms_stage:
            self.movement_prob = self.low_movement_prob
            self.wear_mask = True
            new_SD = True if not self.social_distance else None
            self.social_distance = True
            # print('Hit mild and altruitsic and new SD: {}'.format(new_SD))
        elif self.current_symptom_stage == 'severe' and new_symptoms_stage:
            # Severe means SD and WM and NO non-defensive movement
            # todo: Might turn off ALL movement at this stage
            self.movement_prob = 0.
            self.wear_mask = True
            new_SD = True if not self.social_distance else None
            self.social_distance = True

        # If not dead and end of infection then recovered
        if self.current_infection_stage == 'recover' and new_infection_stage:
            self.recovered = True
            self.infected = False
            self.susceptible = False
            self.wear_mask = self.wear_mask_before_symptoms
            new_SD = self.social_distance_before_symptoms if self.social_distance != self.social_distance_before_symptoms else None
            self.social_distance = self.social_distance_before_symptoms
            self.movement_prob = self.movement_prob_before_symptoms

        return False, new_SD

    # Check if person is infected given the number of infected (and in infectious phase) people
    # in its immediate neighborhood
    def gets_infected(self, num_infectious_neighbors, base_infection_prob, mask_infection_prob_decrease):
        # Skip if already infected or recovered
        if self.infected or self.recovered:
            return
        # Use Kermack-McKendrick Model of infection probability
        # 1 - (1 - p) ^ r; p -> infection prob of one person; r -> number of infectious people
        p = base_infection_prob + -1. * (self.wear_mask * mask_infection_prob_decrease)
        r = num_infectious_neighbors
        I_prob = 1 - (1 - p) ** r
        if np.random.random() < I_prob:
            self.infected = True
            self.current_symptom_stage = self.symptoms_periods[0][0]
            self.current_infection_stage = self.infectious_periods[0][0]
            self.infectious_periods.pop(0)
            self.symptoms_periods.pop(0)
