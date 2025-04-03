from cryptography.fernet import Fernet  # Import the Fernet module for encryption and decryption

# Encrypts the file in this string
your_file = "ENTER YOU FILE PATH / NAME"

# Generate a new encryption key
key = Fernet.generate_key()

# Save the generated key to a file for later decryption
with open("secret.key", "wb") as key_file:
    key_file.write(key)

# Load the encryption key from the file
with open("secret.key", "rb") as key_file:
    key = key_file.read()

# Initialize the Fernet cipher with the loaded key
cipher = Fernet(key)

# Open the image file in binary read mode
with open(your_file, "rb") as file:
    file_data = file.read()  # Read the original file data

# Encrypt the file data using the Fernet cipher
encrypted_data = cipher.encrypt(file_data)

# Overwrite the original file with the encrypted data
with open(your_file, "wb") as file:
    file.write(encrypted_data)

# Print confirmation message
print("The file has been encrypted successfully.")
