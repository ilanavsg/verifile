"""
from Crypto.PublicKey import RSA

# 1. Generate a new private key (2048 bits is standard)
key = RSA.generate(2048)

# 2. Extract the private and public keys
private_key = key.export_key()
public_key = key.publickey().export_key()

# 3. Save them to files (PEM format)
with open("private.pem", "wb") as f:
    f.write(private_key)

with open("public.pem", "wb") as f:
    f.write(public_key)

print("RSA key pair generated and saved successfully!")

"""

