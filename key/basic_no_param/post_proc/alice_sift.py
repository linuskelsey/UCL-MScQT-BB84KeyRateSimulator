def alice_sift(alice_key, keep, results):
    res = [bit for bit, k in zip(alice_key, keep) if k]
    for b in res:
        results.append(b)
    return res