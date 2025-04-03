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

# Create an encryption mapping dictionary
encryption_map = {original: shuffled for original, shuffled in zip(characters, shuffled_characters)}

# Encrypt the message by replacing each character with its mapped value
encrypted_message = "".join(encryption_map[char] for char in user_message)

# Print the encrypted message
print(f"Your encrypted message is: {encrypted_message}")
