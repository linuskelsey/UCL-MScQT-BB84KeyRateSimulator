import threading

from qunetsim.components import Host, Network

from classical.alice_receive_basis import alice_receive_basis
from classical.bob_transmit_basis import bob_transmit_basis
from post_proc.alice_sift import alice_sift
from post_proc.bob_receive_and_sift import bob_receive_and_sift
from quantum.alice_transmit import alice_transmit
from quantum.bob_receive import bob_receive

def main():
    network = Network.get_instance()
    network.start()

    alice = Host('Alice')
    bob = Host('Bob')

    alice.add_connection(bob.host_id)
    bob.add_connection(alice.host_id)

    alice.start()
    bob.start()

    network.add_hosts([alice, bob])

    key_len = 100

    def alice_protocol():
        alice_key, alice_bases = alice_transmit(alice, key_len, 'Bob')
        keep = alice_receive_basis(alice, alice_bases, 'Bob')
        sifted_key = alice_sift(alice_key, keep)

        print("Alice sifted key:", sifted_key)

    def bob_protocol():
        bob_results, bob_bases = bob_receive(bob, key_len, 'Alice')
        bob_transmit_basis(bob, bob_bases, 'Alice')
        sifted_key = bob_receive_and_sift(bob, bob_results, 'Alice')

        print("Bob sifted key:  ", sifted_key)

    alice_thread = threading.Thread(target=alice_protocol)
    bob_thread = threading.Thread(target=bob_protocol)

    alice_thread.start()
    import time
    time.sleep(0.1)  # give Alice a moment to queue qubits
    bob_thread.start()

    alice_thread.join()
    bob_thread.join()

    # Stop hosts
    alice.stop()
    bob.stop()

    # Stop and reset the network singleton
    network.stop(True)   # or network.stop()

if __name__ == "__main__":
    main()