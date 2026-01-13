def encrypt(key: str, text: str):
    encr_text = ""
    key_flat = 0

    # turn string key into single character key
    for char in key:
        key_flat += ord(char)
    key = chr(key_flat)

    # encrypt using single character
    for char in text:
        encr_text += chr(ord(key) ^ ord(char))

    return encr_text

def decrypt(key: str, encr_text: str):
    return encrypt(key, encr_text)