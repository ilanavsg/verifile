import socket
import os
import tkinter as tk
from tkinter import messagebox
from constants import IP, PORT, CYAN, GREEN, RED, YELLOW, RESET, BOLD
from encrypt import Encryption


class Client:
    def __init__(self):
        self.client_socket = None
        self.encryptor = Encryption()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket()
            self.client_socket.connect((IP, PORT))
            print(f"{GREEN}{BOLD}✅ Connected to server at {IP}:{PORT}{RESET}")
        except Exception as e:
            print(f"{RED}❌ Error connecting to server: {e}{RESET}")
            self.client_socket = None

    def show_login_window(self):
        creds = {}

        def login():
            username = entry_user.get()
            password = entry_pass.get()
            if username and password:
                creds["username"] = username
                creds["password"] = password
                root.destroy()
            else:
                messagebox.showerror("Login Failed", "Please enter both username and password")

        root = tk.Tk()
        root.title("Login")
        root.geometry("250x150")

        tk.Label(root, text="Username:").pack(pady=5)
        entry_user = tk.Entry(root)
        entry_user.pack()

        tk.Label(root, text="Password:").pack(pady=5)
        entry_pass = tk.Entry(root, show="*")
        entry_pass.pack()

        tk.Button(root, text="Login", command=login).pack(pady=10)
        root.mainloop()

        return creds.get("username"), creds.get("password")

    def send_client_username_and_password(self):
        user_auth_file = "C:\\Users\\Cyber_User\\Documents\\authentication"

        if os.path.exists(user_auth_file):
            with open(user_auth_file, "r") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    username, password = lines[0], lines[1]
                else:
                    username, password = self.show_login_window()
                    with open(user_auth_file, "w") as fw:
                        fw.write(f"{username}\n{password}")
        else:
            username, password = self.show_login_window()
            with open(user_auth_file, "w") as f:
                f.write(f"{username}\n{password}")

        print(f"{CYAN}🔒 Sending encrypted credentials...{RESET}")
        self.encryptor.send_encrypted_message(self.client_socket, username)
        self.encryptor.send_encrypted_message(self.client_socket, password)

        response = self.encryptor.receive_encrypted_message(self.client_socket)
        print(f"{YELLOW}💬 Server: {response}{RESET}")

    def run(self):
        self.connect_to_server()
        if not self.client_socket:
            print(f"{RED}💤 Client stopped due to connection failure.{RESET}")
            return

        self.send_client_username_and_password()
        client_id = self.encryptor.receive_encrypted_message(self.client_socket)
        print(f"{GREEN}🆔 Assigned client ID: {client_id}{RESET}")
        print(f"{CYAN}✨ Session complete. Closing connection...{RESET}")
        self.client_socket.close()


if __name__ == "__main__":
    Client().run()
