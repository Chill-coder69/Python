import random
import string

# Get the message input from the user
user_message = input("Enter your message: ")

# Create a list of all possible characters (letters, digits, punctuation, and space)
characters = list(string.ascii_letters + string.digits + string.punctuation + " ")

# Set a fixed seed for reproducibility of the shuffle
random.seed(62)

# Create a shuffled copy of the characters list
shuffled_characters = characters.copy()
random.shuffle(shuffled_characters)

# Create a mapping dictionary for decryption
decryption_map = {shuffled: original for original, shuffled in zip(characters, shuffled_characters)}

# Decrypt the message by replacing each character with its mapped value
decrypted_message = "".join(decryption_map.get(char, char) for char in user_message)

# Print the decrypted message
print(f"Your decrypted message is: {decrypted_message}")
