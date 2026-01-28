from typing import List

def bob_error_check(bob_host,
                    key_bits: List[int],
                    alice_id: str,
                    timeout: float = 5.0) -> bool:
    """
    Bob's reactive error-rate estimation using simple string protocol.
    """
    print("\n[Bob] Waiting for Alice's error check request...")

    # Drain old messages first
    drained = []
    while True:
        try:
            msg = bob_host.get_next_classical(alice_id, wait=0)
            drained.append(msg.content)
        except:
            break
    if drained:
        print(f"[Bob] Drained {len(drained)} old messages: {drained[-2:]}")

    # Get the real request with timeout
    try:
        msg_from_alice = bob_host.get_next_classical(alice_id, wait=int(timeout * 1000))
        payload_str = msg_from_alice.content
    except:
        print(f"[Bob] Timeout ({timeout}s) waiting for Alice's error check request.")
        return True

    print(f"[Bob] Received from Alice: '{payload_str}'")

    if not payload_str.startswith("ERR_REQ:"):
        print(f"[Bob] Expected ERR_REQ, got '{payload_str}'")
        return True

    # Parse: "ERR_REQ:3,5,7:1,0,1" -> indices=[3,5,7], alice_bits=[1,0,1]
    # "ERR_REQ:" is 8 characters
    try:
        remainder = payload_str[8:]  # after "ERR_REQ:"
        colon_pos = remainder.rfind(':')  # find LAST colon (separates indices from bits)
        if colon_pos == -1:
            raise ValueError("Missing colon separator between indices and bits")
        
        test_indices_str = remainder[:colon_pos]
        alice_test_bits_str = remainder[colon_pos + 1:]
        
        test_indices = [int(x) for x in test_indices_str.split(",")]
        alice_test_bits = [int(x) for x in alice_test_bits_str.split(",")]
        k = len(test_indices)
        
        if len(alice_test_bits) != k:
            raise ValueError(f"Mismatched lengths: {len(test_indices)} indices, {len(alice_test_bits)} bits")
    except (ValueError, IndexError) as e:
        print(f"[Bob] Failed to parse Alice's request: '{payload_str}' - {e}")
        return True

    n = len(key_bits)
    if n == 0 or k == 0:
        return True

    # Extract Bob's bits
    try:
        bob_test_bits = [key_bits[i] for i in test_indices]
    except IndexError:
        print("[Bob] Index out of range when accessing key bits.")
        return True

    # Send response: "ERR_RESP:0,1,0"
    response_str = f"ERR_RESP:{','.join(map(str, bob_test_bits))}"
    print(f"[Bob] Sending response: '{response_str}'")
    bob_host.send_classical(alice_id, response_str)

    # Local QBER check for logging
    errors = sum(int(a != b) for a, b in zip(alice_test_bits, bob_test_bits))
    qber_est = errors / k
    print(f"[Bob] Error check: tested {k} bits, errors={errors}, QBER={qber_est:.3f}")

    # Remove tested bits from key_bits
    for idx in reversed(sorted(test_indices)):
        del key_bits[idx]

    return False