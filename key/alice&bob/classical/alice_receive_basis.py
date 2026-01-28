def alice_receive_basis(alice, alice_bases, sender):
    n = len(alice_bases)
    keep = [False] * n

    # For each *index* we expect exactly one basis message from Bob
    seen = set()
    print("\n[Alice] Receiving Bob's basis choices...")
    while len(seen) < n:
        msgs = alice.get_classical(sender, wait=10)
        if not msgs:
            # you can add a timeout/abort if needed
            continue

        for m in msgs:
            payload = m.content
            idx_str, bob_basis_str = payload.split(":")
            idx = int(idx_str)
            bob_basis = int(bob_basis_str)

            # Ignore malformed or duplicate indices
            if not (0 <= idx < n) or idx in seen:
                continue

            # Basis comparison for index idx
            check = (alice_bases[idx] == bob_basis)
            keep[idx] = check
            seen.add(idx)

            # Send sifting decision for this specific index
            alice.send_classical(sender, f"{idx}:{int(check)}", await_ack=True)

            if len(seen) == n:
                break
    print("[Alice] Sharing bits to keep...")

    return keep