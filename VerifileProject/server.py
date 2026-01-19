# Ilana Ben Guy
# Project VeriFile

import socket
import threading
from datetime import datetime
import bcrypt
from constants import IP, PORT, CYAN, GREEN, RED, YELLOW, RESET, BOLD, MAX_TOTAL_CONNECTIONS, MAX_CONNECTIONS_PER_IP
from db_manager import DatabaseManager
from create_tables import create_all_tables
from encrypt import Encryption
from install_signature import Signature
from Crypto.Hash import SHA256
import os

PRIVATE_KEY = "C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\private.pem"
PUBLIC_KEY = "C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\public.pem"


class Server:
    def __init__(self):
        self.db_manager = DatabaseManager("localhost", "root", "NewStrongPassword1!", "verifile_db")
        create_all_tables(self.db_manager)
        self.encryptor = Encryption()
        print(f"{CYAN}{BOLD} Database connected and tables verified.{RESET}")

    def image_hash_exists(self, hash_hex):
        existing = self.db_manager.get_rows_with_value("files", "hash_value", hash_hex)
        return bool(existing)

    def handle_upload_for_signature(self, client_socket, user_id):
        try:
            self.encryptor.send_encrypted_message(client_socket, "Send image bytes:")
            filename = self.encryptor.receive_encrypted_message(client_socket)
            img_size_str = self.encryptor.receive_encrypted_message(client_socket)
            if not filename or not img_size_str:
                return
            try:
                img_size = int(img_size_str)
            except:
                self.encryptor.send_encrypted_message(client_socket, "ERROR: Invalid size")
                return

            self.encryptor.send_encrypted_message(client_socket, "READY_FOR_BYTES")

            img_bytes = b""
            while len(img_bytes) < img_size:
                chunk = client_socket.recv(min(4096, img_size - len(img_bytes)))
                if not chunk:
                    break
                img_bytes += chunk

            if len(img_bytes) != img_size:
                self.encryptor.send_encrypted_message(client_socket, "ERROR: Incomplete image")
                return

            temp_path = f"temp_{filename}"
            with open(temp_path, "wb") as f:
                f.write(img_bytes)

            hash_hex = SHA256.new(open(temp_path, "rb").read()).hexdigest()
            if self.image_hash_exists(hash_hex):
                self.encryptor.send_encrypted_message(client_socket, "ERROR: Duplicate image blocked.")
                os.remove(temp_path)
                return

            output_signed = f"signed_{filename}"
            signer = Signature(temp_path, PRIVATE_KEY, PUBLIC_KEY, output_signed)
            signer.install_sign_to_img()
            self.encryptor.send_encrypted_message(client_socket, f"Image signed successfully: {output_signed}")
            price = self.encryptor.receive_encrypted_message(client_socket)
            self.db_manager.insert_row(
                "files",
                "(owner_id, creator_id, original_filename, stored_filename, _type, upload_date, hash_value, signature, watermarked_file, price, status)",
                "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (user_id, user_id, filename, output_signed, "image", datetime.now(), hash_hex, "embedded", output_signed, price, "available")
            )

        except Exception as e:
            print(f"{RED}Upload error: {e}{RESET}")
            try:
                self.encryptor.send_encrypted_message(client_socket, f"ERROR: {e}")
            except:
                pass
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

    def handle_buy_option(self, client_socket):
        images = self.db_manager.get_all_rows("files") 
        for img in images:
            filename = img[4]
            price = str(img[11]) 
            base_dir = r"C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\"
            path = os.path.join(base_dir, filename)
            try:
                with open(path, "rb") as f:
                    import base64
                    data = base64.b64encode(f.read()).decode()
            except:
                data = ""
            self.encryptor.send_encrypted_message(client_socket, filename)
            self.encryptor.send_encrypted_message(client_socket, price)
            self.encryptor.send_encrypted_message(client_socket, data)
        self.encryptor.send_encrypted_message(client_socket, "") 

    def handle_options(self, client_socket, user_id):
        while True:
            try:
                cmd = self.encryptor.receive_encrypted_message(client_socket)
                if not cmd:
                    break
                cmd = cmd.strip()

                if cmd == "1":
                    self.handle_upload_for_signature(client_socket, user_id)
                elif cmd == "2":
                    self.handle_buy_option(client_socket)
                elif cmd == "3":
                    self.encryptor.send_encrypted_message(client_socket, "SELL flow not implemented yet.")
                elif cmd == "4":
                    self.encryptor.send_encrypted_message(client_socket, "Goodbye!")
                    break
                else:
                    self.encryptor.send_encrypted_message(client_socket, "Invalid option.")
            except ConnectionResetError:
                print(f"{YELLOW}Client disconnected abruptly.{RESET}")
                break
            except Exception as e:
                print(f"{RED}Options error: {e}{RESET}")
                break

    def handle_client(self, client_socket):
        try:
            username = self.encryptor.receive_encrypted_message(client_socket)
            password = self.encryptor.receive_encrypted_message(client_socket)
            email = self.encryptor.receive_encrypted_message(client_socket)
            role = self.encryptor.receive_encrypted_message(client_socket)
            if not username or not password:
                client_socket.close()
                return

            existing = self.db_manager.get_rows_with_value("clients", "client_username", username)
            if existing:
                db_password = existing[0][4]
                if bcrypt.checkpw(password.encode(), db_password.encode()):
                    user_id = existing[0][0]
                    self.encryptor.send_encrypted_message(client_socket, "WELCOME BACK")
                    self.encryptor.send_encrypted_message(client_socket, str(user_id))
                    self.handle_options(client_socket, user_id)
                else:
                    self.encryptor.send_encrypted_message(client_socket, "AUTH FAILED")
            else:
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                ip, port = client_socket.getpeername()
                self.db_manager.insert_row(
                    "clients",
                    "(ip, port, client_username, client_password_hash, email, last_visit, role)",
                    "(%s,%s,%s,%s,%s,%s,%s)",
                    (ip, port, username, hashed, email, datetime.now(), role)
                )
                user_id = self.db_manager.get_rows_with_value("clients", "client_username", username)[0][0]
                self.encryptor.send_encrypted_message(client_socket, "NEW USER REGISTERED")
                self.encryptor.send_encrypted_message(client_socket, str(user_id))
                self.handle_options(client_socket, user_id)
        except Exception as e:
            print(f"{RED}Client handler error: {e}{RESET}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def start_server(self):
        server_socket = socket.socket()
        server_socket.bind((IP, PORT))
        server_socket.listen()
        print(f"{CYAN}Server running on {IP}:{PORT}{RESET}")
        connections = {}
        total_connections = 0
        while True:
            client_socket, addr = server_socket.accept()
            ip, port = addr
            if ip not in connections:
                connections[ip] = []
            rows = self.db_manager.get_rows_with_value("clients", "ip", ip)
            if rows:
                ddos_status = rows[0][7]
                if ddos_status:
                    print(f"{RED}Blocked IP tried to connect: {ip}{RESET}")
                    client_socket.close()
                    continue
            if total_connections >= MAX_TOTAL_CONNECTIONS:
                print(f"{RED}Max total connections reached{RESET}")
                client_socket.close()
                continue
            if len(connections[ip]) >= MAX_CONNECTIONS_PER_IP:
                print(f"{RED}DDOS detected from IP {ip}{RESET}")
                for sock in connections[ip]:
                    sock.close()
                connections[ip].clear()
                if rows:
                    user_id = rows[0][0]
                    self.db_manager.update_row(
                        table_name="clients",
                        primary_key_column="user_id",
                        primary_key_value=user_id,
                        column_names=["ddos_status"],
                        column_values=[True]
                    )
                client_socket.close()
                continue
            connections[ip].append(client_socket)
            total_connections += 1
            print(f"{GREEN}Client connected: {addr}{RESET}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()


if __name__ == "__main__":
    Server().start_server()
