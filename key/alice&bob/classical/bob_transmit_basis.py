def bob_transmit_basis(bob, bases, receiver):
    print("[Bob] Transmitting basis choices classically...")
    for i, basis in enumerate(bases):
        bob.send_classical(receiver, f"{i}:{basis}", await_ack=True)