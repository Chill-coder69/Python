from cryptography.fernet import Fernet as F
file = input("Enter your file name : ")
key = F.generate_key()
ft = F(key)
def e():
    if file != "secret.key" and file != "File_Encryption_and_Decryption.py":
        with open(file , "rb") as f:
            File_content = f.read()
        Encrypted_text = ft.encrypt(File_content)
        with open("secret.key","wb") as s:
            s.write(key)
        with open(file, "wb") as f:
            f.write(Encrypted_text)
def d():
    if file != "secret.key" and file != "File_Encryption_and_Decryption.py":
        with open("secret.key" , "rb") as s:
            key = s.read()
        ft = F(key)
        with open(file , "rb") as f:
            Encrypted_text = f.read()
        decrypted_text = ft.decrypt(Encrypted_text)
        with open(file , "wb") as f:
            f.write(decrypted_text)
user =  input("E/D : ")
if user.lower() == "d":
    d()
elif user.lower() == "e":
    e()
