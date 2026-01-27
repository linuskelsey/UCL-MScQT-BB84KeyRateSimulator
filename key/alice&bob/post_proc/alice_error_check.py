import random
from typing import List

def alice_error_check(alice_host,
                      key_bits: List[int],
                      bob_id: str,
                      test_fraction: float = 0.2,
                      qber_threshold: float = 0.11) -> bool:
    """
    Alice's side of BB84 error-rate estimation.

    - Randomly selects a subset of positions from key_bits.
    - Sends indices and Alice's bits at those positions to Bob.
    - Receives Bob's bits at those indices.
    - Computes sample QBER.
    - If QBER > qber_threshold -> return True (abort).
    - Otherwise, removes the tested bits from key_bits in-place and returns False.

    Parameters
    ----------
    alice_host : qunetsim.components.Host
        Alice's host object.
    key_bits : list[int]
        Alice's current sifted key, will be modified in-place.
    bob_id : str
        Host id of Bob (e.g. 'Bob').
    test_fraction : float
        Fraction of bits to sacrifice for parameter estimation.
    qber_threshold : float
        Maximum acceptable quantum bit error rate.

    Returns
    -------
    bool
        True if error rate too high (abort), False if acceptable.
    """
    n = len(key_bits)
    if n == 0:
        # Nothing to test; abort conservatively or just accept.
        return True

    # Number of bits to test, at least 1.
    k = max(1, int(test_fraction * n))
    # Randomly choose k distinct indices.
    test_indices = sorted(random.sample(range(n), k))

    # Prepare Alice's test bits.
    alice_test_bits = [key_bits[i] for i in test_indices]

    # Send test indices and Alice's bits to Bob.
    # We send a simple dict; QuNetSim will pickle it.
    msg_to_bob = {
        'type': 'error_check_request',
        'indices': test_indices,
        'bits': alice_test_bits,
    }
    alice_host.send_classical(bob_id, msg_to_bob)

    # Wait for Bob's reply containing his bits at those indices.
    msg_from_bob = alice_host.get_next_classical_msg(bob_id)
    payload = msg_from_bob.content

    if not isinstance(payload, dict) or payload.get('type') != 'error_check_response':
        # Unexpected message; abort.
        return True

    bob_test_bits = payload.get('bits', [])
    if len(bob_test_bits) != k:
        # Mismatched length; abort.
        return True

    # Compute sample QBER on the tested subset.
    errors = sum(int(a != b) for a, b in zip(alice_test_bits, bob_test_bits))
    qber_est = errors / k

    print(f"[Alice] Error check: tested {k} bits, errors={errors}, QBER={qber_est:.3f}")

    # Remove tested bits from key_bits (in-place) so they are not used in final key.
    # Delete from highest index to lowest so indices stay valid.
    for idx in reversed(test_indices):
        del key_bits[idx]

    # Decide whether to abort.
    if qber_est > qber_threshold:
        print(f"[Alice] QBER {qber_est:.3f} exceeds threshold {qber_threshold:.3f}. Aborting.")
        return True

    print(f"[Alice] QBER {qber_est:.3f} <= threshold {qber_threshold:.3f}. Continuing.")
    return False