def bob_transmit_basis(bob, bases, receiver):
    for i, basis in enumerate(bases):
        bob.send_classical(receiver, f"{i}:{basis}", await_ack=True)