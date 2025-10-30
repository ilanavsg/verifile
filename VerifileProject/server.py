"""
version 1
database
client uploads image, application checks if image isn't
already signed, if not image gets signature.
second client who "bought" the image
wants to upload it to the server and sell it. The application checks using public key
if image hasn't been tampered with.
returns status msg
"""
from db_manager import DatabaseManager
from create_tables import create_all_tables
class Server:
    def __init__(self):
        # Initialize database connection
        self.db_manager = DatabaseManager("localhost", "root", "NewStrongPassword1!", "verifile_db")
        create_all_tables(self.db_manager)

if __name__ == "__main__":
    server = Server()
