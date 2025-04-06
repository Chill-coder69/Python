from cryptography.fernet import Fernet  # Import the Fernet module for encryption and decryption

# Ask user to input the file path
your_file = input("Enter the file path or name you want to encrypt: ").strip()

# Generate a new encryption key
key = Fernet.generate_key()

# Save the generated key to a file for later decryption
with open("secret.key", "wb") as key_file:
    key_file.write(key)

# Initialize the Fernet cipher with the generated key
cipher = Fernet(key)

# Open the file in binary read mode and encrypt its content
try:
    with open(your_file, "rb") as file:
        file_data = file.read()  # Read the original file data
except FileNotFoundError:
    print(f"Error: The file '{your_file}' was not found.")
    exit()

# Encrypt the file data using the Fernet cipher
encrypted_data = cipher.encrypt(file_data)

# Overwrite the original file with the encrypted data
with open(your_file, "wb") as file:
    file.write(encrypted_data)

# Print confirmation message
print("✅ The file has been encrypted successfully.")
