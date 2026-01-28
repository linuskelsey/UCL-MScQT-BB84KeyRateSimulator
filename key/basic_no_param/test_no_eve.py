import threading
import time

from qunetsim.components import Host, Network

from classical.alice_receive_basis import alice_receive_basis
from classical.bob_transmit_basis import bob_transmit_basis
from post_proc.alice_sift import alice_sift
from post_proc.bob_receive_and_sift import bob_receive_and_sift
from quantum.alice_transmit import alice_transmit
from quantum.bob_receive import bob_receive

def test_no_eve():
    network = Network.get_instance()
    network.start()

    alice = Host('Alice')
    bob = Host('Bob')

    alice.add_connection(bob.host_id)
    bob.add_connection(alice.host_id)

    alice.start()
    bob.start()

    network.add_hosts([alice, bob])

    raw_len = 100
    results_alice = []
    results_bob = []

    def alice_protocol():
        alice_key, alice_bases = alice_transmit(alice, raw_len, 'Bob')
        keep = alice_receive_basis(alice, alice_bases, 'Bob')
        sifted_key = alice_sift(alice_key, keep, results_alice)
        # add error check stage here to make sure of no eavesdropper - test_eve.py

        print("Alice sifted key:", sifted_key)

    def bob_protocol():
        bob_raw, bob_bases = bob_receive(bob, raw_len, 'Alice')
        bob_transmit_basis(bob, bob_bases, 'Alice')
        sifted_key = bob_receive_and_sift(bob, bob_raw, 'Alice', results_bob)
        # add error check stage here to make sure of no eavesdropper - test_eve.py

        print("Bob sifted key:  ", sifted_key)

    alice_thread = threading.Thread(target=alice_protocol)
    bob_thread = threading.Thread(target=bob_protocol)

    # start timer before running threads
    start = time.time()

    alice_thread.start()
    time.sleep(0.1)  # give Alice a moment to queue qubits
    bob_thread.start()

    alice_thread.join()
    bob_thread.join()

    # stop timer after running threads
    end = time.time()

    # Stop hosts
    alice.stop()
    bob.stop()

    # Stop and reset the network singleton
    network.stop(True)   # or network.stop()

    if results_alice != results_bob:
        return 'Key mismatch - try again' # automate this in future

    return f"Successful key transmission: {len(results_alice)} bits at secure rate of {len(results_alice) / (end - start)} bits per second."

# needed for multiprocessing
if __name__ == "__main__":
    print(test_no_eve())