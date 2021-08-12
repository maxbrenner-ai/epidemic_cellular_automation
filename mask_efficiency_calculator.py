infectious_neighbors = 3 #max: 8
base_infection_prob = 0.3
mask_infection_prob_decrease = 0.2776022

p = infectious_neighbors*(base_infection_prob+(-1.0*(1*mask_infection_prob_decrease))) 
p = p / infectious_neighbors
probability_of_infection1 = 1-(1-p) ** infectious_neighbors
print("Probability of infection while wearing mask with %i infectious neighbors = %1.5f%%" %(infectious_neighbors, probability_of_infection1)) 

p = infectious_neighbors*(base_infection_prob+(-1.0*(0*mask_infection_prob_decrease))) 
p = p / infectious_neighbors
probability_of_infection0 = 1-(1-p) ** infectious_neighbors
print("Probability of infection while NOT wearing mask with %i infectious neighbors = %1.5f%%" %(infectious_neighbors, probability_of_infection0)) 

mask_effectiveness = 100-(100/probability_of_infection0)*probability_of_infection1
print("Mask effectiveness = %1.5f%%" %mask_effectiveness)



