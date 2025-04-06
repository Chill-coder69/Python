from cryptography.fernet import Fernet  # Import Fernet for encryption/decryption

# Ask user to enter the encrypted file path
your_file = input("Enter your encrypted file path or name: ").strip()

# Load the secret encryption key
try:
    with open("secret.key", "rb") as key_file:
        key = key_file.read()
except FileNotFoundError:
    print("Key file not found. Make sure 'secret.key' exists.")
    exit()

# Initialize Fernet with the key
cipher = Fernet(key)

# Read the encrypted data
try:
    with open(your_file, "rb") as file:
        encrypted_data = file.read()
except FileNotFoundError:
    print(f"File '{your_file}' not found.")
    exit()

# Attempt to decrypt
try:
    decrypted_data = cipher.decrypt(encrypted_data)
except Exception as e:
    print("Decryption failed. Possible reasons: wrong key or file not encrypted.\nError:", e)
    exit()

# Write the decrypted data back to the file
with open(your_file, "wb") as file:
    file.write(decrypted_data)

print("✅ The file has been decrypted successfully.")
