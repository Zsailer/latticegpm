import os
import random

from latticeproteins.fitness import Fitness
from latticeproteins.interactions import miyazawa_jernigan
from latticeproteins.sequences import RandomSequence, NMutants
from latticeproteins.conformations import Conformations

from .thermo import LatticeThermodynamics
from gpmap.utils import hamming_distance
from gpmap.utils import AMINO_ACIDS

def adaptive_walk(lattice, n_mutations):
    """Given a lattice object, adaptive walk to a sequence n_mutations away.
    Only works for <10 conformations in the landscapes!!!
    """
    # Sanity check
    if type(lattice) != LatticeThermodynamics:
        raise TypeError("lattice must be a LatticeThermodynamics object")
    elif len(lattice.conf_list) > 10:
        raise Exception("too many conformations to compute in a reasonable time.")

    wildtype = lattice.sequence
    mutant = list(wildtype)

    hamming = 0
    indices = list(range(len(wildtype)))
    fracfolded = lattice.fracfolded
    while hamming < n_mutations:
        # Select a site to mutate
        mut = mutant[:]
        index = random.choice(indices)

        # Choose a mutation
        mutation = random.choice(AMINO_ACIDS)
        mut[index] = mutation

        # New lattice
        mlattice = LatticeThermodynamics(
            "".join(mut),
            lattice.conf_list,
            lattice.temperature,
            interaction_energies=lattice.interaction_energies)

        if mlattice.fracfolded > fracfolded:
            indices.remove(index)
            mutant[index] = mutation
            hamming = hamming_distance(wildtype, mutant)
            fracfolded = mlattice.fracfolded

    return mlattice



def sequence_space(length, temperature=1.0, threshold=0.0,
    target_conf=None,
    differby=None,
    max_iter=1000,
    interaction_energies=miyazawa_jernigan,
    dGdependence="fracfolded"):
    """Randomly search sequence space for two sequences that
    fold with stability below some threshold and differ at a given number of sites.

    Parameters
    ----------
    Conformations : latticeproteins.conformations.Conformations object
        object that holds all the possible conformations to search.
    temperature : float
        Temperature parameter (ratio to kT)
    threshold : float
        Maximum allowed stability for landscape

    Returns
    -------
    sequences : list of two strings
        List of two sequences that differ at all sites and fold.
    """
    # Make a conformations database.
    database_dir = "database/"
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    # Check differby
    if differby is None:
        differby = length
    elif differby > length:
        raise Exception("differby cannot be larger than the length of the sequences.")
    # Construct conformations database.
    conformations = Conformations(length, database_dir, interaction_energies=miyazawa_jernigan)
    # Set the fitness.
    fitness = Fitness(temperature, conformations,
        dGdependence=dGdependence,
        targets=target_conf)
    # Find a sequence that's below a certain energy.
    energy = threshold
    counter = -1
    while energy >= threshold:
        sequence = RandomSequence(length)
        energy = fitness.Stability(sequence)
        # Check looping
        if counter >= max_iter:
            print(energy)
            raise Exception("Reached max iteration in search.")
    # Set the resulting sequence as the first variable
    sequence1 = ''.join(sequence)
    energy = threshold # Reset energy
    # Search for next function
    counter = -1
    mutants = NMutants(sequence1, differby, max_iter)
    while energy >= threshold:
        counter += 1
        sequence = RandomSequence(length)
        energy = fitness.Stability(sequence)
        # Check looping
        if counter >= max_iter:
            raise Exception("Reached max iteration in search.")
    # Set second sequence
    sequence2 = ''.join(mutants[counter])
    return sequence1, sequence2
