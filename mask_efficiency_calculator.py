# This may all be wrong. Please check

'''
Regarding the value of 'mask_infection_prob_decrease':

A randomized controlled trial of 2862 healthcare personnel reported no significant
differences in laboratory-confirmed influenza infection among users wearing N95
or surgical masks, with incidence rates of 8.2% and 7.2%, respectively.
Others found wearing an N95 -or- surgical mask reduced the risk of SARS
transmission by approximately 80%, compared to not wearing a mask.
Thus, for the general public, a value that results in a mean of 80% seems accurate enough.
- Keeping that in mind, 0.362 seems good.
Results for cloth masks vary widely. I presume a value with a mean between 50% and 80% seems ok.
- Therefore 0.315 is a good value.

    Source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8084286/
'''

infectious_neighbors_max = 8  # maximum possible neighbors is 8
infectious_neighbors = 1
base_infection_prob = 0.4
mask_infection_prob_decrease = 0.362
# with base_infection_prob = 0.4, a value of 0.362 seems good for simulating
# N95 and surgical masks being worn by layman. 0.315 seems good for cloth masks

while infectious_neighbors <= infectious_neighbors_max:
    p = infectious_neighbors*(base_infection_prob+(-1.0*(1*mask_infection_prob_decrease)))
    p = p / infectious_neighbors
    probability_of_infection1 = 1-(1-p) ** infectious_neighbors
    # print("Probability of infection while wearing mask with %i infectious neighbors = %1.5f%%" %(infectious_neighbors, probability_of_infection1))

    p = infectious_neighbors*(base_infection_prob+(-1.0*(0*mask_infection_prob_decrease)))
    p = p / infectious_neighbors
    probability_of_infection0 = 1-(1-p) ** infectious_neighbors
    # print("Probability of infection while NOT wearing mask with %i infectious neighbors = %1.5f%%" %(infectious_neighbors, probability_of_infection0))

    mask_effectiveness = 100-(100/probability_of_infection0)*probability_of_infection1
    if infectious_neighbors == 1:
        print("Mask effectiveness vs probability of infection is ...")
    if infectious_neighbors == 1 or infectious_neighbors == 8:
        print("- %1.5f%% with %i infectious neighbors." % (mask_effectiveness, infectious_neighbors))
    infectious_neighbors = infectious_neighbors + 1
