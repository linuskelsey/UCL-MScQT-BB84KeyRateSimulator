from typing import List

def bob_error_check(bob_host,
                    key_bits: List[int],
                    alice_id: str) -> bool:
    """
    Bob's side of BB84 error-rate estimation.

    - Waits for Alice's error_check_request (indices + Alice's bits).
    - Extracts Bob's bits at those indices and sends them back.
    - Removes the tested bits from key_bits in-place.
    - Optionally recomputes QBER locally for logging.
    - Returns False if message was handled correctly, True if something went wrong.

    Parameters
    ----------
    bob_host : qunetsim.components.Host
        Bob's host object.
    key_bits : list[int]
        Bob's current sifted key, will be modified in-place.
    alice_id : str
        Host id of Alice (e.g. 'Alice').

    Returns
    -------
    bool
        True if an error occurred (abort), False otherwise.
    """
    # Wait for Alice's request.
    msg_from_alice = bob_host.get_next_classical_msg(alice_id)
    payload = msg_from_alice.content

    if not isinstance(payload, dict) or payload.get('type') != 'error_check_request':
        print("[Bob] Unexpected message type during error check.")
        return True

    test_indices = payload.get('indices', [])
    alice_test_bits = payload.get('bits', [])

    if len(test_indices) != len(alice_test_bits):
        print("[Bob] Mismatched indices and bits length from Alice.")
        return True

    k = len(test_indices)
    n = len(key_bits)
    if n == 0 or k == 0:
        # Nothing meaningful to test; abort conservatively.
        return True

    # Extract Bob's bits at those indices.
    try:
        bob_test_bits = [key_bits[i] for i in test_indices]
    except IndexError:
        print("[Bob] Index out of range when accessing key bits.")
        return True

    # Send response back to Alice.
    response = {
        'type': 'error_check_response',
        'bits': bob_test_bits,
    }
    bob_host.send_classical(alice_id, response)

    # Optionally, compute and print QBER locally for sanity.
    errors = sum(int(a != b) for a, b in zip(alice_test_bits, bob_test_bits))
    qber_est = errors / k
    print(f"[Bob] Error check: tested {k} bits, errors={errors}, QBER={qber_est:.3f}")

    # Remove tested bits from key_bits (in-place) so they are not used in final key.
    for idx in reversed(sorted(test_indices)):
        del key_bits[idx]

    # Bob itself does not make the threshold decision; Alice's function does that.
    # Return False to indicate no local error.
    return False