# Ilana Ben Guy
# Project VeriFile
import re
import tkinter as tk
from tkinter import Label, scrolledtext, Toplevel, Listbox, Button
from PIL import Image, ImageTk
import time
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
import io
import base64
import json

PRIVATE_KEY = "C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\private.pem"
PUBLIC_KEY = "C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\public.pem"


class Server:
    def __init__(self):
        self.db_manager = DatabaseManager("localhost", "root", "NewStrongPassword1!", "verifile_db")
        create_all_tables(self.db_manager)
        self.encryptor = Encryption()
        print(f"{CYAN}{BOLD} Database connected and tables verified.{RESET}")
        # Initialize GUI components
        self.root = tk.Tk()
        self.root.withdraw()
        self.log_text = None
        self.client_listbox = None
        self.bg_image = None
        self.client_details_images = {}

    def update_gui_log(self, message):
        self.root.after(0, self._update_gui_log, message)

    def _update_gui_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.yview(tk.END)

    def update_client_list(self):
        self.root.after(0, self._update_client_list)

    def _update_client_list(self):
        self.client_listbox.delete(0, tk.END)
        clients = self.db_manager.get_all_rows("clients")
        for client in clients:
            self.client_listbox.insert(tk.END, client[0])

    def show_client_details(self, client_id):
        client_data = self.db_manager.get_rows_with_value("clients", "user_id", client_id)
        if not client_data:
            return
        client = client_data[0]

        details_window = Toplevel()
        details_window.title(f"Client {client_id} Details")
        details_window.geometry("400x350")

        details = [
            f"ID: {client[0]}",
            f"IP: {client[1]}",
            f"Port: {client[2]}",
            f"Last Seen: {client[6]}",
            f"Balance: {client[9]}"
        ]

        for detail in details:
            lbl = Label(details_window, text=detail, fg='white', bg='black')
            lbl.pack(anchor="w", padx=10, pady=2)

        history_button = Button(details_window, text="History", command=lambda: self.show_client_history(client_id), bg='gray', fg='white')
        history_button.pack(pady=10)

    def show_client_history(self, client_id):
        history_window = Toplevel()
        history_window.title(f"Client {client_id} - History")
        history_window.geometry("600x400")

        history_label = Label(history_window, text=f"Client {client_id} Image History", font=("Arial", 12, "bold"), fg="white", bg="black")
        history_label.pack(pady=5)

        image_listbox = Listbox(history_window, height=15, width=80, bg="black", fg="white", selectbackground="gray")
        image_listbox.pack(padx=10, pady=5, expand=True, fill="both")

        images = self.db_manager.get_my_works(client_id)

        if not images:
            image_listbox.insert(tk.END, "No images found for this client.")
        else:
            for img in images:
                image_listbox.insert(tk.END, img)

            def open_selected_image(event):
                selected_index = image_listbox.curselection()
                if selected_index:
                    selected_path = images[selected_index[0]]
                    os.system(f'"{selected_path}"')

            image_listbox.bind("<Double-Button-1>", open_selected_image)

    def image_hash_exists(self, hash_hex):
        existing = self.db_manager.get_rows_with_value("files", "hash_value", hash_hex)
        return bool(existing)

    def handle_upload_for_signature(self, client_socket, user_id):
        try:
            all_works = []
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

    def handle_buy_option(self, client_socket, user_id):
        foreign_works = self.db_manager.get_available_foreign_works(user_id)
        files_dict = {}

        base_dir = r"C:\\Users\\Cyber_User\\Desktop\\verifile\\VerifileProject\\"

        for file_id, owner_id, filename, price in foreign_works:
            stored_filename = filename
            price = price
            path = os.path.join(base_dir, stored_filename)

            thumbnail_b64 = ""
            try:
                with Image.open(path) as im:
                    im.thumbnail((150, 150))
                    buf = io.BytesIO()
                    im.save(buf, format="PNG")
                    thumbnail_b64 = base64.b64encode(buf.getvalue()).decode()
            except Exception as e:
                print(f"Error loading {stored_filename}: {e}")

            self.encryptor.send_encrypted_message(client_socket, stored_filename)
            self.encryptor.send_encrypted_message(client_socket, str(price))
            self.encryptor.send_encrypted_message(client_socket, thumbnail_b64)
            files_dict[stored_filename] = (path, price, owner_id)

        self.encryptor.send_encrypted_message(client_socket, "")

        server_msg = self.encryptor.receive_encrypted_message(client_socket)
        if not server_msg:
            return

        parts = server_msg.split(":", 1)
        if parts[0] == "BUY" and parts[1] in files_dict:
            full_path, price, original_owner = files_dict[parts[1]]
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT balance FROM clients WHERE user_id = %s", (user_id,))
            balance_rows = cursor.fetchall()
            if not balance_rows:
                self.encryptor.send_encrypted_message(client_socket, "FAILED: no balance")
                return
            balance = balance_rows[0][0]
            if balance < price:
                self.encryptor.send_encrypted_message(client_socket, "FAILED: insufficient funds")
                return
            new_balance = balance - price
            self.db_manager.update_row("clients", "user_id", user_id, ["balance"], [new_balance])

            if original_owner:
                owner_rows = self.db_manager.get_column_values_by_user_id("clients", "balance", original_owner)
                if owner_rows:
                    owner_balance = owner_rows[0][0]
                    self.db_manager.update_row("clients", "user_id", original_owner, ["balance"], [owner_balance + price])

            self.db_manager.update_row(
                "files",
                "stored_filename",
                parts[1],
                ["owner_id", "status"],
                [user_id, "sold"]
            )

            try:
                self.encryptor.send_encrypted_message(client_socket, "SUCCESS")
                self.send_file_to_client(client_socket, full_path)
            except Exception as e:
                print(f"Error sending file {full_path}: {e}")
                self.encryptor.send_encrypted_message(client_socket, f"FAILED: {e}")

        else:
            self.encryptor.send_encrypted_message(client_socket, "")

    def send_file_to_client(self, client_socket, full_path):
        try:
            filesize = os.path.getsize(full_path)
            filename = os.path.basename(full_path)

            # Tell client to expect file
            self.encryptor.send_encrypted_message(client_socket, f"{filename}|{filesize}")
            ack = self.encryptor.receive_encrypted_message(client_socket)
            if ack != "READY":
                print("Client not ready")
                return

            # Send file in chunks
            with open(full_path, "rb") as f:
                while chunk := f.read(4096):
                    client_socket.sendall(chunk)

        except Exception as e:
            print(f"Error sending file {full_path}: {e}")
            try:
                self.encryptor.send_encrypted_message(client_socket, "FAILED")
            except:
                pass

    def handle_sell_action(self, client_socket, user_id):
        temp_path = None
        try:
            user_rows = self.db_manager.get_rows_with_value("clients", "user_id", user_id)
            if not user_rows:
                self.encryptor.send_encrypted_message(client_socket, "ERROR: User not found")
                return

            self.encryptor.send_encrypted_message(client_socket, "SEND_IMAGE")
            filename = self.encryptor.receive_encrypted_message(client_socket)
            size = int(self.encryptor.receive_encrypted_message(client_socket))
            self.encryptor.send_encrypted_message(client_socket, "READY")

            existing_files = self.db_manager.get_rows_with_value("files", "stored_filename", filename)
            for f in existing_files:
                if f[1] == user_id and f[-1] == "available":
                    self.encryptor.send_encrypted_message(client_socket, "ERROR: This file is already on sale")
                    return

            img_bytes = b""
            while len(img_bytes) < size:
                chunk = client_socket.recv(min(4096, size - len(img_bytes)))
                if not chunk:
                    raise ConnectionError("Client disconnected during image upload")
                img_bytes += chunk

            temp_path = f"sell_{filename}"
            with open(temp_path, "wb") as f:
                f.write(img_bytes)

            hash_hex = SHA256.new(img_bytes).hexdigest()
            verifier = Signature(temp_path, None, PUBLIC_KEY)
            verified, msg = verifier.verify_signature(temp_path)
            signature_hex = Image.open(temp_path).info.get("Signature")

            self.db_manager.insert_row(
                "history_table",
                "(file_id, user_id, action, hash_value, signature, verified, created_at)",
                "(%s,%s,%s,%s,%s,%s,%s)",
                (None, user_id, "verify", hash_hex, signature_hex, verified, datetime.now())
            )

            if not verified:
                self.encryptor.send_encrypted_message(client_socket, "FAILED")
                self.encryptor.send_encrypted_message(client_socket, "Image not signed or signature invalid")
                return

            price = self.encryptor.receive_encrypted_message(client_socket)
            price = float(price)

            self.db_manager.update_row(
                "files",
                "stored_filename",
                filename,
                ["owner_id", "price", "status", "upload_date", "hash_value", "signature"],
                [user_id, price, "available", datetime.now(), hash_hex, "embedded"]
            )

            self.db_manager.update_row(
                "clients",
                "user_id",
                user_id,
                ["role"],
                ["seller"]
            )

            self.encryptor.send_encrypted_message(client_socket, "SUCCESS")
            self.encryptor.send_encrypted_message(client_socket, "Verified and relisted successfully")

        except Exception as e:
            self.encryptor.send_encrypted_message(client_socket, f"ERROR: {e}")
            self.encryptor.send_encrypted_message(client_socket, "An error occured")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def handle_verify_action(self, client_socket, user_id):
        temp_path = None
        try:
            self.encryptor.send_encrypted_message(client_socket, "SEND_IMAGE")
            filename = self.encryptor.receive_encrypted_message(client_socket)
            size = int(self.encryptor.receive_encrypted_message(client_socket))

            self.encryptor.send_encrypted_message(client_socket, "READY")
            img_bytes = b""
            while len(img_bytes) < size:
                img_bytes += client_socket.recv(4096)

            temp_path = f"verify_{filename}"
            with open(temp_path, "wb") as f:
                f.write(img_bytes)
            # hash
            hash_hex = SHA256.new(img_bytes).hexdigest()
            # verify signature
            verifier = Signature(temp_path, None, PUBLIC_KEY)
            verified, msg = verifier.verify_signature(temp_path)
            # try to resolve file_id (optional but ideal)
            rows = self.db_manager.get_rows_with_value("files", "hash_value", hash_hex)
            file_id = rows[0][0] if rows else None
            signature_hex = Image.open(temp_path).info.get("Signature")
            self.db_manager.insert_row(
                "history_table",
                "(file_id, user_id, action, hash_value, signature, verified, created_at)",
                "(%s,%s,%s,%s,%s,%s,%s)",
                (
                    file_id,
                    user_id,
                    "verify",
                    hash_hex,
                    signature_hex,
                    verified,
                    datetime.now()
                )
            )

            self.encryptor.send_encrypted_message(
                client_socket,
                "VALID" if verified else "INVALID"
            )
            self.encryptor.send_encrypted_message(client_socket, msg)

        except Exception as e:
            self.encryptor.send_encrypted_message(client_socket, f"ERROR: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def handle_options(self, client_socket, user_id):
        while True:
            try:
                cmd = self.encryptor.receive_encrypted_message(client_socket)
                if not cmd:
                    break
                cmd = cmd.strip()

                if cmd == "1":
                    self.update_gui_log(f"Client {user_id} chose option UPLOAD.")
                    self.handle_upload_for_signature(client_socket, user_id)
                elif cmd == "2":
                    self.update_gui_log(f"Client {user_id} chose option BUY.")
                    self.handle_buy_option(client_socket, user_id)
                elif cmd == "3":
                    self.update_gui_log(f"Client {user_id} chose option SELL.")
                    self.handle_sell_action(client_socket, user_id)
                elif cmd == "4":
                    self.update_gui_log(f"Client {user_id} chose option Verify")
                    self.handle_verify_action(client_socket, user_id)
                elif cmd == "5":
                    self.encryptor.send_encrypted_message(client_socket, "Goodbye!")
                    self.update_gui_log(f"Client {user_id} disconnected.")
                    break
                else:
                    self.encryptor.send_encrypted_message(client_socket, "Invalid option.")
            except ConnectionResetError:
                self.update_gui_log(f"Client disconnected abruptly.")
                break
            except Exception as e:
                self.update_gui_log(f"Options error: {e}")
                break

    def handle_client(self, client_socket):
        try:
            username = self.encryptor.receive_encrypted_message(client_socket)
            password = self.encryptor.receive_encrypted_message(client_socket)
            email = self.encryptor.receive_encrypted_message(client_socket)
            role = self.encryptor.receive_encrypted_message(client_socket)

            if not username or not password or not email:
                client_socket.close()
                return

            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

            if len(password) < 8 or not re.match(email_pattern, email):
                self.encryptor.send_encrypted_message(client_socket, "INVALID_FORMAT")
                self.update_gui_log(f"Connection rejected for '{username}': Invalid email or password format.")
                client_socket.close()
                return

            existing = self.db_manager.get_rows_with_value("clients", "client_username", username)
            if existing:
                user_id = existing[0][0]
                db_password = existing[0][4]
                if bcrypt.checkpw(password.encode(), db_password.encode()):
                    self.encryptor.send_encrypted_message(client_socket, "WELCOME")
                    client_status = "EXISTING"
                    self.encryptor.send_encrypted_message(client_socket, str(user_id))
                    all_works = self.db_manager.get_my_works(user_id)
                    payload = json.dumps(all_works)
                    self.encryptor.send_encrypted_message(client_socket, f"WORKS:{payload}")
                else:
                    self.encryptor.send_encrypted_message(client_socket, "AUTH FAILED")
                    client_status = "AUTH FAILED"
                    self.update_gui_log(f"Client {user_id} connected - Status: {client_status}")
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
                client_status = "NEW"
                self.encryptor.send_encrypted_message(client_socket, str(user_id))
                all_works = self.db_manager.get_my_works(user_id)
                payload = json.dumps(all_works)
                self.encryptor.send_encrypted_message(client_socket, f"WORKS:{payload}")

            self.update_gui_log(f"Client {user_id} connected - Status: {client_status}")
            self.update_client_list()
            self.handle_options(client_socket, user_id)

        except Exception as e:
            self.update_gui_log(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
                self.update_client_list()
            except:
                pass

    def create_gui(self):
        # Create splash screen
        splash = Toplevel()
        splash.geometry("400x400")
        splash.overrideredirect(True)

        # Load and keep reference to splash image
        logo = Image.open(r"C:\Users\Cyber_User\Downloads\VerifileLogo.png").resize((400, 400)) #new pic
        logo_photo = ImageTk.PhotoImage(logo)
        label = Label(splash, image=logo_photo)
        label.image = logo_photo  # Keep reference
        label.pack()

        splash.update()
        time.sleep(4)
        splash.destroy()

        # Destroy the initial withdrawn root and create a new one
        self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Server GUI")
        self.root.geometry("500x500")

        # Create scrolled text for logs
        self.log_text = scrolledtext.ScrolledText(self.root, state=tk.DISABLED, wrap=tk.WORD, height=10, bg='black', fg='white')
        self.log_text.pack(expand=True, fill='both', padx=10, pady=5)

        # Create clients label
        Label(self.root, text="VeriFile Customers", font=("Arial", 14, "bold"), fg="white", bg="black").pack(pady=5)

        # Create client listbox
        self.client_listbox = Listbox(self.root, bg='black', fg='white')
        self.client_listbox.pack(expand=True, fill='both', padx=10, pady=5)
        self.client_listbox.bind("<Double-Button-1>", lambda event: self.show_client_details(self.client_listbox.get(self.client_listbox.curselection())))

        # Start server in a separate thread
        threading.Thread(target=self.start_server, daemon=True).start()
        self.root.mainloop()

    def start_server(self):
        server_socket = socket.socket()
        server_socket.bind((IP, PORT))
        server_socket.listen()
        self.update_gui_log("Server started...")
        self.update_gui_log(f"Server running on {IP}:{PORT}")
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
                if ddos_status and ip != '127.0.0.1':
                    self.update_gui_log(f"{RED}Blocked IP tried to connect: {ip}{RESET}")
                    client_socket.close()
                    continue
            if total_connections >= MAX_TOTAL_CONNECTIONS:
                self.update_gui_log(f"{RED}Max total connections reached{RESET}")
                client_socket.close()
                continue
            if len(connections[ip]) >= MAX_CONNECTIONS_PER_IP:
                self.update_gui_log(f"{RED}DDOS detected from IP {ip}{RESET}")
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
            self.update_gui_log(f"Client connected: {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()


if __name__ == "__main__":
    server = Server()
    server.create_gui()
