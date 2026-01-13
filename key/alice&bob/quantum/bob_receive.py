import random

def bob_receive(bob, key_length, sender):
    results = []
    bases = []

    for _ in range(key_length):
        # select next qubit in sender's queue
        qubit = bob.get_qubit(sender, wait=True)

        # choose and record random measurement basis
        basis = random.randint(0,1)
        bases.append(basis)

        # basis-flip if appropriate
        if basis == 1:
            qubit.H()
        
        # measure and store bit value
        result = qubit.measure()
        results.append(result)

    return results, bases