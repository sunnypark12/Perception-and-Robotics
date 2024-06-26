# -*- coding: utf-8 -*-
"""project1.ipynb

## Introduction

In this project, we will be building a (simulated) trash sorting robot as illustrated in the [textbook](http://www.roboticsbook.org/intro.html) for this course. In this scenario, the robot tries to sort trash of some pre-determined categories into corresponding bins. Please refer to [Chapter 2](http://www.roboticsbook.org/S20_sorter_intro.html) of the book for a more detailed description of the scenario. **This project is basically based on Chapter 2 of the textbook. Please use the same values in the textbook for each TODO.**

**However, instead of using gtsam library, we will implement DiscreteDistribution, DiscreteConditional, and GaussianConditional classes ourselves. Please read the comments to understand each function.**

First, import some useful libraries.
"""

#export
import numpy as np
import math
from enum import Enum


from project1_test import TestProject1
from project1_test import verify

np.random.seed(3630)
unit_test = TestProject1()

"""**Useful Global Variables:**"""

#export
class Trash(Enum):
    CARDBOARD = 0
    PAPER = 1
    CAN = 2
    SCRAP_METAL = 3
    BOTTLE = 4

# All possible actions/bins (nop means no action)
ACTIONS = ['glass_bin', 'metal_bin', 'paper_bin', 'nop']
# Categories of trash
Category = ['cardboard', 'paper', 'can', 'scrap_metal', 'bottle']
# Two conductivity states
Conductivity = ["false", "true"]
# Detection states
Detection = ['bottle', 'cardboard', 'paper']
# Appromixations of each category given 1000 pieces of trash
Appromixation = [200, 300, 250, 200, 50]

"""**IMPORTANT NOTE: Please use the variables provided for the results of each of the TODOs.**
## Modeling the World State ([Book Section 2.1](http://www.roboticsbook.org/S21_sorter_state.html))
- Functions to complete: **TODO 1 - TODO 4**
- Objective: Representing the prior probabilities of the trash categories and simulate it by sampling. Please use the prior probabilities provided in the textbook

** DiscreteDistribution **
"""
#export
# Probability distribution of a discrete variable.
class DiscreteDistribution:
  def __init__(self, prior_names, prior):
    '''
    Constructor
        Parameters:
            prior_names (list[str]): list of prior category names
            prior (list[float]): prior probablity/samples for each category
    '''
    self._names = prior_names.copy()
    self._prior = np.array(prior, dtype=float)
    self._prior /= self._prior.sum()

  def get_name_index(self, name) -> int:
    '''
    Helper function to get index of prior name
    '''
    return self._names.index(name)

  def pmf(self) -> list:
    return self._prior

  # sample item
  def sample(self) -> int:
    '''
    Return a sample with the prior probabilities

        Parameters:
            None

        Returns:
            sampled_index (int): an int indicating the sampled item name,
                you may use the helper function to get index of a name
    '''
    sampled_index = np.random.choice(len(self._prior), p=self._prior)
    return sampled_index

# Sanity check to test your Discrete Distribution
print("Testing your Discrete Distribution implementation: ")
def local_test_discrete_distribution():
    categories = ['A', 'B', 'C']
    prior_probabilities = [0.3, 0.4, 0.3]

    distribution = DiscreteDistribution(prior_names=categories, prior=prior_probabilities)

    assert np.isclose(np.sum(distribution.pmf()), 1.0), "Probabilities do not sum to 1"

    sampled_value = distribution.sample()
    assert sampled_value in range(len(categories)), f"Sampled value {sampled_value} is out of range"

    category_to_check = 'B'
    index = distribution.get_name_index(category_to_check)
    assert index == categories.index(category_to_check), f"Index for {category_to_check} is incorrect"

    print("Sanity check passed successfully.")

local_test_discrete_distribution()

#export
# Prior probabilities
def get_category_prior():
    '''
    Returns the prior probabilities of the trash categories.

        Parameters:
            None

        Returns:
            category_prior (DiscreteDistribution): a DiscreteDistribution
                that summarizes the prior probabilities of all trash categories
    '''
    prior_probabilities = [float(x) for x in "200/300/250/200/50".split('/')]
    category_prior = DiscreteDistribution(Category, prior_probabilities)
    return category_prior

# Prior probabilities PMF
def get_category_prior_pmf():
    '''
    Returns the probability mass function (PMF) of the prior probabilities
    of the trash categories.

        Parameters:
            None

        Returns:
            category_prior_pmf (list[float]): a list of the PMF
    '''
    category_prior_pmf = get_category_prior().pmf()
    return list(category_prior_pmf)

print("Testing your prior probabilities of the trash categories: ")
print(verify(unit_test.test_get_category_prior_pmf, get_category_prior_pmf))

#export
def sample_category():
    '''
    Returns a sample of trash category by sampling with the prior probabilities
    of the trash categories

        Parameters:
            None

        Returns:
            sample (int): an int indicating the sampled trash category
    '''
    CDF = np.cumsum(get_category_prior_pmf())
    u = np.random.rand()

    for sample in range(5):
        if u < float(CDF[sample]):
            return sample

print("Testing your sample of trash category: ", verify(unit_test.test_sample_category, sample_category))

"""## Sensors for Sorting Trash
- Objective: Representing conditional probabilities of sensors and simulate them by sampling

Complete DiscreteConditional
"""

#export
# Conditional probability of P(A | B), where both A and B are discrete variables.
class DiscreteConditional:
  def __init__(self, A_names, B_names, cpt):
    '''
    Constructor
        Parameters:
            A_names (list[str]): names of possible values of A
            B_names (list[str]): names of possible values of B
            cpt (list[list[float]]): conditional probability table, represented by a 2D list
    '''
    self._B_names = B_names.copy()
    self._A_names = A_names.copy()
    self._cpt = np.array(cpt, dtype=float)
    self._cpt /= np.sum(self._cpt, axis=1)[:, np.newaxis]

  def get_A_index(self, A_name) -> int:
    return self._A_names.index(A_name)

  # sample value of A given value of B
  def sample(self, B_index: int) -> int:
    '''
    Returns a sample of A using the conditional probability distribution
    given the value of B

        Parameters:
            B_index(int): Given value of B (represented by an index)

        Returns:
            sampled_index (int): an int indicating the sampled item name,
                you may use the helper function to get index of A
    '''
    probabilities = self._cpt[B_index, :]
    sampled_index = np.random.choice(len(self._A_names),  p=probabilities)
    return sampled_index

  # likelihoods of B given the value of A
  def likelihoods(self, A_index: int) -> list:
    '''
    Returns the likelihoods of all categories given the value of A

        Parameters:
            A_index (int): value of A (represented as an index)

        Returns:
            likelihoods (list[float] or np.ndarray): a list of likelihoods of each category
    '''
    likelihoods = self._cpt[:, A_index]
    likelihoods /= np.sum(likelihoods)
    return likelihoods

# Sanity check to test your Discrete Conditional implementation
def local_test_discrete_conditional():
    B_categories = ['B0', 'B1']
    A_categories = ['A0', 'A1', 'A2']
    cpt_matrix = np.array([[0.2, 0.5, 0.3],
                           [0.6, 0.2, 0.2]])

    conditional_distribution = DiscreteConditional(A_categories,
                                                   B_categories,
                                                   cpt=cpt_matrix)

    assert np.allclose(np.sum(conditional_distribution._cpt, axis=1), 1.0), "Conditional probabilities do not sum to 1"

    B_index_to_sample = 0
    sampled_A_index = conditional_distribution.sample(B_index_to_sample)
    assert sampled_A_index in range(len(A_categories)), f"Sampled A index {sampled_A_index} is out of range"

    A_index_to_check = 1
    likelihoods = conditional_distribution.likelihoods(A_index_to_check)
    assert np.isclose(np.sum(likelihoods / np.sum(likelihoods)), 1.0), "Likelihoods do not sum to 1 for the specified A index"

    print("Sanity check passed successfully.")

local_test_discrete_conditional()

"""Complete GaussianConditiona"""

#export
# Conditional probability of P(A | B), where B is a discrete
# variable, and A is a continuous variable under Gaussian distribution.
class GaussianConditional:
    def __init__(self, B_names, means, sigmas):
      '''
      Constructor
          Parameters:
              B_names (list[str]): list of prior category names
              means (list[float]): list of mean measurement given each category
              sigmas (list[float]): list of measurement standard deviation given each category
      '''
      self._B_names = B_names.copy()
      self._means = means
      self._sigmas = sigmas

    @staticmethod
    def Gaussian(x, mu=0.0, sigma=1.0):
      return np.exp(-0.5 * (x - mu) ** 2 / sigma ** 2) / np.sqrt(2 * np.pi * sigma ** 2)

    # sample A given B
    def sample(self, B_index):
        '''
        Returns a sample of weight using the conditional probability given
        the prior name index.

            Parameters:
                B_index (int): given value of B (represented by an index)

            Returns:
                weight (float): a float indicating the sampled weight
        '''
        # Get the mean and sigma
        mean = self._means[B_index]
        sigma = self._sigmas[B_index]
        # Sample from the Gaussian distribution
        weight = np.random.normal(mean, sigma)
        return weight

    # likelihoods of A given B
    def likelihoods(self, B_value: float) -> list:
      '''
      Returns the likelihoods of A given B

          Parameters:
              B_value (float): a float indicating the value of B

          Returns:
              likelihoods (list[float] or np.ndarray): a list of likelihoods of A
      '''
      likelihoods = [self.Gaussian(B_value, mu, sigma) for mu, sigma in zip(self._means, self._sigmas)]
      return likelihoods

"""Declare conditional objects for sensor data"""

# 1. Conductivity - binary sensor
def get_pCT():
    '''
    Returns P(Conductivity | Trash Category)

        Parameters:
            None

        Returns:
            pCT (DiscreteConditional): a DiscreteConditional that
                indicates the conditinal probability of conductivity given
                the trash category
    '''

    prob_distribution = [
        [0.99, 0.01],  # Cardboard
        [0.99, 0.01], # Paper
        [0.1, 0.9],  # Can
        [0.15, 0.85],  # Scrap Metal
        [0.95, 0.05]   # Bottle
    ]
    pCT = DiscreteConditional(Conductivity, Category, prob_distribution)
    return pCT


# 2. Detection - multi-valued sensor
def get_pDT():
    '''
    Returns P(Detection | Trash Category)

        Parameters:
            None

        Returns:
            pDT (DiscreteConditional): a DiscreteConditional that
                indicates the conditinal probability of camera detection
                given the trash category
    '''

    prob_distribution = [
        [0.02, 0.88, 0.1],  # Cardboard
        [0.02, 0.2, 0.78], # Paper
        [0.33, 0.33, 0.34],  # Can
        [0.33, 0.33, 0.34],  # Scrap Metal
        [0.95, 0.02, 0.03]   # Bottle
    ]
    pDT = DiscreteConditional(Detection, [Category], prob_distribution)
    return pDT

# 3. Weight - continuous-valued sensor
def get_pWT():
    '''
    Returns P(Weight | Trash Category)

        Parameters:
            None

        Returns:
            pWT (GaussianConditional): a GaussianConditional object which represents
            prior name, mean, and sigma of each category for Gaussian distribution
    '''
    pWT = np.array([[20, 10], [5, 5], [15, 5], [150, 100], [300, 200]])
    return pWT

def sample_conductivity(category=None):
    '''
    Returns a sample of conductivity using the conditional probability
    given the trash category.
    If the category parameter is None, sample a category first.

        Parameters:
            category (int): an int indicating the trash category

        Returns:
            conductivity (int): an int indicating the conductivity, with
                0 being nonconductive and 1 being conductive
    '''
    pCT = get_pCT()
    if category is None:

        pCategory = get_category_prior()
        category = pCategory.sample()

    conductivity = pCT.sample(category)
    return conductivity

print("Testing your sample conductivity: ", verify(unit_test.test_sample_conductivity, sample_conductivity))

def sample_detection(category=None):
    '''
    Returns a sample of detection using the conditional probability given
    the trash category.
    If the category parameter is None, sample a category first.

        Parameters:
            category (int): an int indicating the trash category

        Returns:
            detection (int): an int indicating the sampled detection
    '''
    if category is None:
        category = sample_category()

    # Get the conditional probability distribution
    pDT = get_pDT()

    # Sample a detection outcome
    detection = pDT.sample(category)
    return detection

print("Testing your sample detection: ", verify(unit_test.test_sample_detection, sample_detection))

#export
def sample_weight(category=None):
    '''
    Returns a sample of weight using the conditional probability given
    the trash category.
    If the category parameter is None, sample a category first.

        Parameters:
            category (int): an int indicating the trash category

        Returns:
            weight (float): a float indicating the sampled weight
    '''
    weight = np.random.normal(*get_pWT()[category])
    return weight

print("Testing your sample weight: ", verify(unit_test.test_sample_weight, sample_weight))


#export
def likelihood_no_sensors():
    '''
    Returns the likelihoods of all trash categories using only priors,
    aka no sensors.

        Parameters:
            None

        Returns:
            likelihoods (list[float]): a list of likelihoods of each trash category
    '''
    likelihoods = get_category_prior_pmf()
    return likelihoods

print("Testing your likelihoods with no sensors: ")
print(verify(unit_test.test_likelihood_no_sensor, likelihood_no_sensors))


#export
def likelihood_given_weight(weight):
    '''
    Returns the likelihoods of all trash categories using only the weight
    sensor (no priors)

        Parameters:
            weight (float): a float indicating the weight of trash

        Returns:
            likelihoods (list[float] or np.ndarray): a list of likelihoods of each trash category
    '''
    pWC = np.array([[20, 10], [5, 5], [15, 5], [150, 100], [300, 200]])
    likelihoods = np.array([GaussianConditional.Gaussian(weight, *pWC[index]) for index in range(5)])
    return likelihoods

print("Testing your likelihoods using only the weight sensor: ")
print(verify(unit_test.test_likelihood_given_weight, likelihood_given_weight))


#export
def likelihood_given_detection(detection):
    '''
    Returns the likelihoods of all trash categories using only the detection
    sensor (no priors)

        Parameters:
            detection (int): an int indicating the sampled detection

        Returns:
            likelihoods (list[float] or np.ndarray): a list of likelihoods of each trash category
    '''
    pDT = get_pDT()
    likelihoods = np.array([pDT._cpt[category][detection] for category in range(len(Category))])
    return np.array(likelihoods)

print("Testing your likelihoods using only the detection sensor: ")
print(verify(unit_test.test_likelihood_given_detection, likelihood_given_detection))


#export
def bayes_given_weight(weight):
    '''
    Returns the posteriors of all trash categories by combining the weight
    sensor and the priors

        Parameters:
            weight (float): a float indicating the weight of the trash

        Returns:
            posteriors (list[float] or np.ndarray): a list of posterior probabilities of each trash category
    '''
    unormalized = likelihood_given_weight(weight) * get_category_prior_pmf()
    posteriors = [float(i) / sum(unormalized) for i in unormalized]
    return posteriors

print("Testing your posteriors with the weight sensor and priors: ")
print(verify(unit_test.test_bayes_given_weight, bayes_given_weight))


#export
# Bayes with three sensors
def bayes_given_three_sensors(conductivity, detection, weight):
    '''
    Returns the posteriors of all trash categories by combining all three
    sensors and the priors

        Parameters:
            conductivity (int): an int indicating the conductivity, with
                0 being nonconductive and 1 being conductive

            detection (int): an int indicating the sampled detection

            weight (float): a float indicating the weight of the trash

        Returns:
            posteriors (list[float] or np.ndarray): a list of posterior probabilities of each trash category
    '''

    likelihood_conductivity = np.array(get_pCT().likelihoods(conductivity))
    likelihood_detection = np.array(likelihood_given_detection(detection))
    likelihood_weight = np.array(likelihood_given_weight(weight))
    prior_pmf = np.array(get_category_prior_pmf())

    combined = likelihood_conductivity * likelihood_detection * likelihood_weight
    unnormalized = combined * prior_pmf
    posteriors = unnormalized / unnormalized.sum()
    return posteriors

print("Testing your posteriors giving all three sensors: ")
print(verify(unit_test.test_bayes_given_three_sensors, bayes_given_three_sensors))

"""## Decision Theory
- Objective: Incorporating the cost table with the perception to reach a final sorting decision
"""

# Cost table for each state
COST_TABLE = np.array([[2,  2,  4,  6,  0],
                       [1,  1,  0,  0,  2],
                       [0,  0,  5, 10,  3],
                       [1,  1,  1,  1,  1]])

### DECISION ###
def make_decision(posteriors):
    '''
    Returns the decision made by the robot given the likelihoods/posteriors you calculated

        Parameters:
            posteriors (list[float]): a list of posteriors of each trash category

        Returns:
            action (int): an int indicating the action taken by the robot
    '''
    action = np.argmin(COST_TABLE @ posteriors)
    return action

print("Testing the decision made by your robot: ")
print(verify(unit_test.test_make_decision, make_decision))

unit_test.get_cost_table(COST_TABLE)
print("Testing your cost without sensors: ")
print(verify(unit_test.test_score_likelihood_no_sensor, likelihood_no_sensors, make_decision))
print("Testing your cost using the weight sensor:")
print(verify(unit_test.test_score_likelihood_given_weight, likelihood_given_weight, make_decision))
print("Testing your cost using the detection sensor:")
print(verify(unit_test.test_score_likelihood_given_detection, likelihood_given_detection, make_decision))
print("Testing your cost using with the weight sensor and priors:")
print(verify(unit_test.test_score_bayes_given_weight, bayes_given_weight, make_decision))
print("Testing your cost using all three sensors: ")
print(verify(unit_test.test_score_bayes_given_three_sensors, bayes_given_three_sensors, make_decision))

"""A Gaussian distribution, also known as a normal distribution, is an inappropriate distribution to represent
the weight of an item. This is because it has an infinite range and therefore sampling from it can produce
a negative number, while an item cannot have a negative weight. """

#export
def fit_log_normal(data):
    '''
    Returns mu, sigma for a log-normal distribution

        Parameters:
            data (list[float]): A list of positive floats that represent the weight of an item

        Returns:
            mu (float), sigma (float): The mu and sigma for a log-normal distribution
    '''
    data = [math.log(i) for i in data]
    mu = np.mean(data)
    sigma = math.sqrt(np.var(data))
    return mu, sigma

print("Testing your log-normal distribution: ", verify(unit_test.test_fit_log_normal, fit_log_normal))
