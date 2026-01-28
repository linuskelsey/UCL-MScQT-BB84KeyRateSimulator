import random
from typing import List

def alice_error_check(alice_host,
                      key_bits: List[int],
                      bob_id: str,
                      test_fraction: float = 0.2,
                      qber_threshold: float = 0.11,
                      timeout: float = 5.0) -> bool:
    """
    Alice's side of BB84 error-rate estimation using simple string protocol.
    """
    print("\n[Alice] Preparing for error reconciliation...")
    n = len(key_bits)
    if n == 0:
        return True

    # Drain old messages first
    print("[Alice] Draining old classical messages...")
    drained = []
    while True:
        try:
            msg = alice_host.get_next_classical(bob_id, wait=0)
            drained.append(msg.content)
        except:
            break
    if drained:
        print(f"[Alice] Drained {len(drained)} old messages: {drained[-2:]}")

    k = max(1, int(test_fraction * n))
    test_indices = sorted(random.sample(range(n), k))
    alice_test_bits = [key_bits[i] for i in test_indices]

    # Send: "ERR_REQ:3,5,7:1,0,1"
    indices_str = ','.join(map(str, test_indices))
    bits_str = ','.join(map(str, alice_test_bits))
    msg_str = f"ERR_REQ:{indices_str}:{bits_str}"
    
    print(f"[Alice] Sending error check request: '{msg_str}'")
    alice_host.send_classical(bob_id, msg_str)

    # Wait for Bob's response with timeout
    try:
        msg_from_bob = alice_host.get_next_classical(bob_id, wait=int(timeout * 1000))
        payload_str = msg_from_bob.content
    except:
        print(f"[Alice] Timeout waiting for Bob's response.")
        return True
    
    print(f"\n[Alice] Received from Bob: '{payload_str}'")
    
    if not payload_str.startswith("ERR_RESP:"):
        print(f"[Alice] Expected ERR_RESP, got '{payload_str}'")
        return True
    
    # Parse Bob's bits
    try:
        bob_test_bits_str = payload_str[9:]  # after "ERR_RESP:"
        bob_test_bits = [int(x) for x in bob_test_bits_str.split(",")]
        if len(bob_test_bits) != k:
            print(f"[Alice] Expected {k} bits from Bob, got {len(bob_test_bits)}")
            return True
    except (ValueError, IndexError):
        print(f"[Alice] Failed to parse Bob's response: '{payload_str}'")
        return True

    # Compute QBER
    errors = sum(int(a != b) for a, b in zip(alice_test_bits, bob_test_bits))
    qber_est = errors / k

    print(f"[Alice] Error check: tested {k} bits, errors={errors}, QBER={qber_est:.3f}")

    # Remove tested bits from key_bits (highest index first)
    for idx in reversed(test_indices):
        del key_bits[idx]

    # Threshold decision
    if qber_est > qber_threshold:
        print(f"[Alice] QBER {qber_est:.3f} > threshold {qber_threshold:.3f}. Aborting.")
        return True

    print(f"[Alice] QBER {qber_est:.3f} <= threshold {qber_threshold:.3f}. Continuing.")
    return False