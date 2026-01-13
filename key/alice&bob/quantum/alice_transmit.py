import random
from qunetsim.objects import Qubit

def alice_transmit(alice, key_length, receiver):
    key = []
    bases = []

    for _ in range(key_length):
        # generate random bit and polarisation
        bit = random.randint(0,1)
        basis = random.randint(0,1)

        # store bit and basis
        key.append(bit)
        bases.append(basis)

        # init qubit
        qubit = Qubit(alice)

        # perform bit- and basis-flips if necessary
        if bit == 1:
            qubit.X()

        if basis == 1:
            qubit.H()

        # send qubit to Bob
        alice.send_qubit(receiver, qubit, await_ack=True)
    
    return key, bases