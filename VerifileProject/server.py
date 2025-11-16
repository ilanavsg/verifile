# Ilana Ben Guy
# Project VeriFile
"""
Version 0
Database: clients, files, keys. (created)
Basic Structure:
    Client uploads image, application checks if image isn't
    already signed, if not image gets signature.
    Second client who "bought" the image ( his role is "seller" )
    wants to upload it to the server and sell it.
    The application checks using public key if image hasn't been tampered with.
    returns status msg
"""
import socket
import threading
from datetime import datetime
import bcrypt
from constants import IP, PORT, CYAN, GREEN, RED, YELLOW, MAGENTA, RESET, BOLD
from db_manager import DatabaseManager
from create_tables import create_all_tables
from encrypt import Encryption
from install_signature import Signature
import os

PRIVATE_KEY = "C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\private.pem"
PUBLIC_KEY = "C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\public.pem"


class Server:
    def __init__(self):
        self.db_manager = DatabaseManager("localhost", "root", "NewStrongPassword1!", "verifile_db")
        create_all_tables(self.db_manager)
        self.encryptor = Encryption()
        print(f"{CYAN}{BOLD} Database connected and tables verified.{RESET}")

    def handle_client(self, client_socket):
        try:
            print(f"{YELLOW} Handling new client connection...{RESET}")
            username = self.encryptor.receive_encrypted_message(client_socket)
            password = self.encryptor.receive_encrypted_message(client_socket)
            email = self.encryptor.receive_encrypted_message(client_socket)
            role = self.encryptor.receive_encrypted_message(client_socket)
            client_ip, client_port = client_socket.getpeername()

            existing = self.db_manager.get_rows_with_value("clients", "client_username", username)

            if existing:
                db_password_hash = existing[0][4]
                db_username = existing[0][3]
                if db_username == username and bcrypt.checkpw(password.encode('utf-8'), db_password_hash.encode('utf-8')):
                    self.db_manager.update_row(
                        "clients",
                        "client_username",
                        username,
                        ["last_visit", "ip", "port"],
                        [datetime.now(), client_ip, client_port]
                    )
                    client_id = existing[0][0]
                    print(f"{GREEN} Returning user authenticated: {username} (ID {client_id}){RESET}")
                    self.encryptor.send_encrypted_message(client_socket, "WELCOME BACK")
                    self.encryptor.send_encrypted_message(client_socket, str(client_id))
                    self.handle_options(client_socket)

                else:
                    print(f"{RED} Authentication failed for user: {username}{RESET}")
                    self.encryptor.send_encrypted_message(client_socket, "AUTHENTICATION FAILED")
            else:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                self.db_manager.insert_row(
                    "clients",
                    "(ip, port, client_username, client_password_hash, email, last_visit, role)",
                    "(%s,%s,%s,%s,%s,%s,%s)",
                    (client_ip, client_port, username, hashed_password, email, datetime.now(), role)
                )
                new_client = self.db_manager.get_rows_with_value("clients", "client_username", username)
                client_id = new_client[0][0]
                print(f"{MAGENTA} New user registered: {username} (ID {client_id}){RESET}")
                self.encryptor.send_encrypted_message(client_socket, "NEW USER REGISTERED")
                self.encryptor.send_encrypted_message(client_socket, str(client_id))
                self.handle_options(client_socket)

        except Exception as e:
            print(f"{RED} Error handling client: {e}{RESET}")
        finally:
            print(f"{YELLOW} Connection closed for client.{RESET}")
            client_socket.close()

    def handle_upload_for_signature(self, client_socket):
        """
        Receives an image sent from the client (as bytes),
        generates a digital signature, applies a watermark,
        and saves the signed image on the server.
        """
        self.encryptor.send_encrypted_message(client_socket, f"{YELLOW}Send image bytes:")
        filename = self.encryptor.receive_encrypted_message(client_socket)
        img_size_str = self.encryptor.receive_encrypted_message(client_socket)
        img_size = int(img_size_str)
        self.encryptor.send_encrypted_message(client_socket, "READY_FOR_BYTES")

        img_bytes = b""
        while len(img_bytes) < img_size:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            img_bytes += chunk

        temp_path = f"temp_{filename}"
        with open(temp_path, "wb") as f:
            f.write(img_bytes)
        output_signed = f"signed_{filename}"
        try:
            signer = Signature(
                img_path=temp_path,
                private_key_path=PRIVATE_KEY,
                public_key_path=PUBLIC_KEY,
                watermarked_path=output_signed
            )
            signer.install_sign_to_img()
            self.encryptor.send_encrypted_message(client_socket, f"Image signed successfully as {output_signed}")
        except Exception as e:
            self.encryptor.send_encrypted_message(client_socket, f"ERROR: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def handle_options(self, client_socket):
        """
        Sends the available actions to an authenticated client and waits for a
        command selection. The available options include:

            1. Upload an image to receive a digital signature.
            2. Upload a signed image for verification and selling.
            3. Exit the session.

        The server receives the client's selection and processes it accordingly.
        Communication is fully encrypted through the Encryption module.
        """
        while True:
            menu = (
                f"{CYAN}===== VeriFile Menu =====\n"
                f"{CYAN}1. Upload image for signing\n"
                f"{CYAN}2. Exit\n"
                f"{YELLOW}Choose an option:"
            )
            self.encryptor.send_encrypted_message(client_socket, menu)
            cmd = self.encryptor.receive_encrypted_message(client_socket)
            if cmd == "1":
                self.handle_upload_for_signature(client_socket)
                continue
            elif cmd == "2":
                self.encryptor.send_encrypted_message(client_socket, "Goodbye!")
                break
            else:
                self.encryptor.send_encrypted_message(client_socket, "Invalid option.")

    def start_server(self):
        server_socket = socket.socket()
        server_socket.bind((IP, PORT))
        server_socket.listen()
        print(f"{CYAN}{BOLD} Server started — waiting for connections on {IP}:{PORT}...{RESET}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"{GREEN} Client connected: {addr}{RESET}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()


if __name__ == "__main__":
    Server().start_server()
