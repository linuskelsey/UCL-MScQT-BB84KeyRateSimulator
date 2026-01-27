def bob_receive_and_sift(bob, bob_measured, sender, results):
    n = len(bob_measured)
    keep = [False] * n

    seen = set()
    while len(seen) < n:
        msgs = bob.get_classical(sender, wait=10)
        if not msgs:
            continue

        for m in msgs:
            payload = m.content
            idx_str, check_str = payload.split(":")
            idx = int(idx_str)
            if not (0 <= idx < n) or idx in seen:
                continue

            check = bool(int(check_str))
            keep[idx] = check
            seen.add(idx)

            if len(seen) == n:
                break

    res = [bit for bit, k in zip(bob_measured, keep) if k]
    for b in res:
        results.append(b)
    return res