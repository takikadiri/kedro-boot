"""
This is a boilerplate pipeline 'monte_carlo'
generated using Kedro 0.18.14
"""

import random
from typing import List


def simulate_distance(radius: float):
    x = random.uniform(0, radius)  # Generate a random x-coordinate between 0 and 1
    y = random.uniform(0, radius)  # Generate a random y-coordinate between 0 and 1
    distance = x**2 + y**2  # Calculate the distance from the origin (0,0)
    return distance


def estimate_pi(simulation_distances: List[float], radius: float, num_samples: int):
    inside_circle = 0

    for distance in simulation_distances:
        if distance <= radius:
            inside_circle += 1

    estimated_pi = (inside_circle / num_samples) * 4
    return estimated_pi
