def alice_sift(alice_key, keep):
    return [bit for bit, k in zip(alice_key, keep) if k]