import threading
import time

from qunetsim.components import Host, Network

from classical.alice_receive_basis import alice_receive_basis
from classical.bob_transmit_basis import bob_transmit_basis
from post_proc.alice_sift import alice_sift
from post_proc.bob_receive_and_sift import bob_receive_and_sift
from post_proc.alice_error_check import alice_error_check
from post_proc.bob_error_check import bob_error_check
from quantum.alice_transmit import alice_transmit
from quantum.bob_receive import bob_receive

def test_eve():
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
    res_a = []
    res_b = []
    abort = {'value': False}

    def alice_protocol():
        alice_key, alice_bases = alice_transmit(alice, raw_len, 'Bob')
        keep = alice_receive_basis(alice, alice_bases, 'Bob')
        sifted_key = alice_sift(alice_key, keep, res_a)

        try:
            a_err = alice_error_check(alice, res_a, 'Bob')
        except Exception as e:
            print(f"[Alice] Error check crashed: {e}")
            abort['value'] = True
            return
        
        if a_err:
            abort['value'] = True
            return
        print("Alice sifted key:", sifted_key)

    def bob_protocol():
        bob_raw, bob_bases = bob_receive(bob, raw_len, 'Alice')
        bob_transmit_basis(bob, bob_bases, 'Alice')
        sifted_key = bob_receive_and_sift(bob, bob_raw, 'Alice', res_b)

        # Small delay so Alice's message arrives first
        time.sleep(0.2)

        try:
            b_err = bob_error_check(bob, res_b, 'Alice')
        except Exception as e:
            print(f"[Bob] Error check crashed: {e}")
            abort['value'] = True
            return
        
        if b_err:
            abort['value'] = True
            return
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

    if abort['value']:
        return "Aborted: error rate too high, possible eavesdropper."

    # Stop hosts
    alice.stop()
    bob.stop()

    # Stop and reset the network singleton
    network.stop(True)   # or network.stop()

    if res_a != res_b:
        return "Aborted: key mismatch" # automate this in future

    return f"Successful key transmission: {len(res_a)} bits at secure rate of {len(res_a) / (end - start)} bits per second."

# needed for multiprocessing
if __name__ == "__main__":
    print(test_eve())