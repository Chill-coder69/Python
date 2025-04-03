from cryptography.fernet import Fernet  # Import the Fernet module for encryption and decryption

# Dencrypts the file in this string
your_file = "ENTER YOU FILE PATH / NAME"

# Load the secret encryption key from a file
with open("secret.key", "rb") as key_file:
    key = key_file.read()

# Initialize the Fernet cipher with the loaded key
cipher = Fernet(key)

# Open the encrypted image file in binary read mode
with open(your_file, "rb") as file:
    encrypted_data = file.read()

# Decrypt the data using the Fernet cipher
decrypted_data = cipher.decrypt(encrypted_data)

# Write the decrypted data back to the same file, effectively restoring the original image
with open(your_file, "wb") as file:
    file.write(decrypted_data)

# Print confirmation message
print("The file has been decrypted successfully.")
