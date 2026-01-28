import sys
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

def fibre_transmittance(alpha_db_per_km=0.2, L_km=10.0):
    """
    Photon survival probability after L km.
    
    With high-performant standards of alpha=0.1dB/km, T is 0.8 for L=10km and drops to 0.1 for L=100km.
    """
    return 10 ** (-alpha_db_per_km * L_km / 10.0)

def key_transmit(bit_count: int,
                 min_key_len=10,
                 alpha_dp_per_km=0.2,
                 L_km=10.0
                 ):

    T = fibre_transmittance(alpha_dp_per_km, L_km)
    photon_count = int(2 * (bit_count / 0.8)) # / 0.8 as 0.2 of sifted key used for reconciliation; 2 * as sifted key is 0.5 * photon_count on average.
    print(f"\nExpected key length: {T * photon_count * 0.8 * 0.5}")
    if T * photon_count * 0.8 * 0.5 < min_key_len:
        return f"Restart with lower loss or length fibre, or minimum key length.\n"
    
    print("\n[NET] Setting up network instance...")
    network = Network.get_instance()
    network.start()

    alice = Host('Alice')
    bob = Host('Bob')

    alice.add_connection(bob.host_id)
    bob.add_connection(alice.host_id)

    alice.start()
    bob.start()

    network.add_hosts([alice, bob])

    print("[NET] Network prepared and hosts added.")

    raw_len = photon_count
    res_a = []
    res_b = []
    abort = {'value': False}

    def alice_protocol():
        alice_key, alice_bases = alice_transmit(alice, raw_len, 'Bob')
        keep = alice_receive_basis(alice, alice_bases, 'Bob')
        alice_sift(alice_key, keep, res_a)

        try:
            a_err = alice_error_check(alice, res_a, 'Bob')
        except Exception as e:
            print(f"[Alice] Error check crashed: {e}")
            abort['value'] = True
            return
        
        if a_err:
            abort['value'] = True
            return

    def bob_protocol():
        bob_raw, bob_bases = bob_receive(bob, raw_len, 'Alice')
        bob_transmit_basis(bob, bob_bases, 'Alice')
        bob_receive_and_sift(bob, bob_raw, 'Alice', res_b)

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

    key = ''
    for bit in res_a[:bit_count]:
        key += str(bit)

    return f"\nSuccessful key transmission: {len(key)} bits (out of a requested {bit_count}) at secure rate of {round(len(res_a) / (end - start),3)} bits per second.\nSifted and error reconciled key: {key}\n"

# needed for multiprocessing
if __name__ == "__main__":
    bit_count = int(input("\nHow many bits would you roughly like in your key? "))
    min_len = int(input("What is your minimum possible key length? (press return for default=10) "))
    alpha = float(input("What is the loss of your fibre in dB per km? (press return for default=0.2) "))
    L = float(input("What is the length of your fibre in km? (press return for default=10.0) "))
    print(key_transmit(bit_count, min_len, alpha, L))