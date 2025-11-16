import socket
import os
import tkinter as tk
from tkinter import messagebox, ttk
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
            print(f"{GREEN}{BOLD} Connected to server at {IP}:{PORT}{RESET}")
        except Exception as e:
            print(f"{RED} Error connecting to server: {e}{RESET}")
            self.client_socket = None

    def show_login_window(self):
        creds = {}

        def login():
            username = entry_user.get()
            password = entry_pass.get()
            email = entry_email.get() # dont forget to check later that email is existent! (and also in the right format)
            role = role_combobox.get()
            if username and password and email and role:
                creds["username"] = username
                creds["password"] = password
                creds["email"] = email
                creds["role"] = role
                root.destroy()
            else:
                messagebox.showerror("Login Failed", "Please fill in all fields")

        root = tk.Tk()
        root.title("Login")
        root.geometry("280x320")


        tk.Label(root, text="Username:").pack(pady=5)
        entry_user = tk.Entry(root)
        entry_user.pack()

        tk.Label(root, text="Password:").pack(pady=5)
        entry_pass = tk.Entry(root, show="*")
        entry_pass.pack()

         # Email
        tk.Label(root, text="Email:").pack(pady=5)
        entry_email = tk.Entry(root)
        entry_email.pack()

        tk.Label(root, text="Role:").pack(pady=5)
        role_combobox = ttk.Combobox(root, values=["buyer", "seller", "admin"], state="readonly")
        role_combobox.pack()
        role_combobox.set("buyer")  # Default value

        tk.Button(root, text="Login", command=login).pack(pady=15)

        root.mainloop()

        return (
            creds.get("username"),
            creds.get("password"),
            creds.get("email"),
            creds.get("role")
        )

    def send_client_info(self):
        user_auth_file = "C:\\Users\\Cyber_User\\Documents\\authentication"

        if os.path.exists(user_auth_file):
            with open(user_auth_file, "r") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    username, password, email, role = lines[0], lines[1], lines[2] , lines[3]
                else:
                    username, password, email, role = self.show_login_window()
                    with open(user_auth_file, "w") as fw:
                        fw.write(f"{username}\n{password}\n{email}\n{role}")
        else:
            username, password, email, role = self.show_login_window()
            with open(user_auth_file, "w") as f:
                f.write(f"{username}\n{password}\n{email}\n{role}")

        print(f"{CYAN} Sending encrypted credentials...{RESET}")
        self.encryptor.send_encrypted_message(self.client_socket, username)
        self.encryptor.send_encrypted_message(self.client_socket, password)
        self.encryptor.send_encrypted_message(self.client_socket, email)
        self.encryptor.send_encrypted_message(self.client_socket, role)
        response = self.encryptor.receive_encrypted_message(self.client_socket)
        print(f"{YELLOW}{response}{RESET}")

    def send_image_bytes(self, file_path):
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            data = f.read()

        # Tell server file name
        self.encryptor.send_encrypted_message(self.client_socket, filename)

        # Tell server number of bytes
        self.encryptor.send_encrypted_message(self.client_socket, str(len(data)))

        # Wait for confirmation
        ready = self.encryptor.receive_encrypted_message(self.client_socket)
        if ready != "READY_FOR_BYTES":
            print("Server not ready to receive bytes")
            return

        # Send actual bytes (not encrypted for binary compatibility)
        self.client_socket.sendall(data)

    def run(self):
        self.connect_to_server()
        if not self.client_socket:
            print(f"{RED}💤 Client stopped due to connection failure.{RESET}")
            return

        self.send_client_info()
        client_id = self.encryptor.receive_encrypted_message(self.client_socket)
        print(f"{GREEN} Assigned client ID: {client_id}{RESET}")

        while True:
            server_menu = self.encryptor.receive_encrypted_message(self.client_socket)
            print(server_menu)

            client_ans = input().strip()
            self.encryptor.send_encrypted_message(self.client_socket, client_ans)

            if client_ans == "1":
                server_msg = self.encryptor.receive_encrypted_message(self.client_socket)
                print(server_msg)
                file_path = input("Enter local image path: ").strip()
                if not os.path.exists(file_path):
                    print(f"{RED}❌ File does not exist.")
                    continue
                self.send_image_bytes(file_path)
                response = self.encryptor.receive_encrypted_message(self.client_socket)
                print(f"{response}")

            elif client_ans == "2":
                response = self.encryptor.receive_encrypted_message(self.client_socket)
                print(f"{CYAN} {response} Session complete. Closing connection...{RESET}")
                break

            else:
                response = self.encryptor.receive_encrypted_message(self.client_socket)
                print(f"{RED}{response}Unknown command!")
        self.client_socket.close()



if __name__ == "__main__":
    Client().run()
