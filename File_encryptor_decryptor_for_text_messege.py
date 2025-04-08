import random
import string

def e():
    user_message = input("Enter your message: ")
    characters = list(string.ascii_letters + string.digits + string.punctuation + " ")
    random.seed(62)
    shuffled_characters = characters.copy()
    random.shuffle(shuffled_characters)
    encryption_map = {original: shuffled for original, shuffled in zip(characters, shuffled_characters)}
    encrypted_message = "".join(encryption_map[char] for char in user_message)
    print(f"Your encrypted message is: {encrypted_message}")

def d():
    user_message = input("Enter your message: ")
    characters = list(string.ascii_letters + string.digits + string.punctuation + " ")
    random.seed(62)
    shuffled_characters = characters.copy()
    random.shuffle(shuffled_characters)
    decryption_map = {shuffled: original for original, shuffled in zip(characters, shuffled_characters)}
    decrypted_message = "".join(decryption_map.get(char, char) for char in user_message)
    print(f"Your decrypted message is: {decrypted_message}")

what = input("E/D : ")
if what.lower() == "e":
    e()
elif what.lower() == "d":
    d()
