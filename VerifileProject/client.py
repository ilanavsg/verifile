import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from constants import IP, PORT, CYAN, GREEN, RED, YELLOW, RESET, BOLD
from encrypt import Encryption


class Client:
    def __init__(self):
        self.host = IP
        self.port = PORT
        self.client_socket = None
        self.encryptor = Encryption()
        self.root = None
        self.username = ""
        self.client_id = None

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket()
            self.client_socket.connect((self.host, self.port))
            print(f"{GREEN}Connected to server{RESET}")
        except Exception as e:
            messagebox.showerror("Connection error", str(e))

    def send_client_info(self):
        auth_file = "C:\\Users\\Cyber_User\\Documents\\authentication"
        if os.path.exists(auth_file):
            lines = open(auth_file).read().splitlines()
            if len(lines) >= 4:
                self.username, password, email, role = lines[0], lines[1], lines[2], lines[3]
            else:
                self.username, password, email, role = self.show_login_window()
                open(auth_file, "w").write(f"{self.username}\n{password}\n{email}\n{role}")
        else:
            self.username, password, email, role = self.show_login_window()
            open(auth_file, "w").write(f"{self.username}\n{password}\n{email}\n{role}")

        self.encryptor.send_encrypted_message(self.client_socket, self.username)
        self.encryptor.send_encrypted_message(self.client_socket, password)
        self.encryptor.send_encrypted_message(self.client_socket, email)
        self.encryptor.send_encrypted_message(self.client_socket, role)

        resp1 = self.encryptor.receive_encrypted_message(self.client_socket)
        resp2 = self.encryptor.receive_encrypted_message(self.client_socket)
        if resp2:
            self.client_id = int(resp2)

    def show_login_window(self):
        creds = {}

        def submit():
            creds["username"] = e_user.get()
            creds["password"] = e_pass.get()
            creds["email"] = e_email.get()
            creds["role"] = role_var.get()
            login.destroy()

        login = tk.Tk()
        login.title("Login")
        login.geometry("320x280")
        login.config(bg="#ffe6f0")
        tk.Label(login, text="Username:", bg="#ffe6f0").pack(pady=5)
        e_user = tk.Entry(login)
        e_user.pack()
        tk.Label(login, text="Password:", bg="#ffe6f0").pack(pady=5)
        e_pass = tk.Entry(login, show="*")
        e_pass.pack()
        tk.Label(login, text="Email:", bg="#ffe6f0").pack(pady=5)
        e_email = tk.Entry(login)
        e_email.pack()
        tk.Label(login, text="Role:", bg="#ffe6f0").pack(pady=5)
        role_var = tk.StringVar(value="buyer")
        tk.OptionMenu(login, role_var, "buyer", "seller", "admin").pack()
        tk.Button(login, text="Login", command=submit, bg="#ffd1dc").pack(pady=12)
        login.mainloop()
        return creds.get("username"), creds.get("password"), creds.get("email"), creds.get("role")

    def send_image_bytes(self, path):
        try:
            filename = os.path.basename(path)
            data = open(path, "rb").read()
            self.encryptor.send_encrypted_message(self.client_socket, filename)
            self.encryptor.send_encrypted_message(self.client_socket, str(len(data)))
            ready = self.encryptor.receive_encrypted_message(self.client_socket)
            if ready != "READY_FOR_BYTES":
                return
            self.client_socket.sendall(data)
        except Exception as e:
            messagebox.showerror("Upload error", str(e))

    def run_gui(self):
        self.root = tk.Tk()
        self.root.title("VeriFile Marketplace")
        self.root.geometry("450x400")
        self.root.config(bg="#fff0f5")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        tk.Label(self.root, text=f"Welcome! {self.username}", font=("Arial", 18), bg="#fff0f5", fg="#ff66b2").pack(pady=10)

        self.menu_label = tk.Label(self.root, text="", font=("Consolas", 11), bg="#fff0f5", justify="left")
        self.menu_label.pack(pady=5)

        tk.Button(self.root, text="Upload", width=28, command=self.upload_action, bg="#ffd1dc").pack(pady=5)
        tk.Button(self.root, text="Buy", width=28, command=self.buy_action, bg="#ffe6f0").pack(pady=5)
        tk.Button(self.root, text="Sell", width=28, command=self.sell_action, bg="#ffe6f0").pack(pady=5)
        tk.Button(self.root, text="Exit", width=28, command=self.exit_app, bg="#ffb3cc").pack(pady=15)

        try:
            menu = self.encryptor.receive_encrypted_message(self.client_socket)
            if menu:
                self.menu_label.config(text=menu)
        except:
            pass

        self.root.mainloop()

    def refresh_menu(self):
        try:
            menu = self.encryptor.receive_encrypted_message(self.client_socket)
            if menu:
                self.menu_label.config(text=menu)
        except:
            pass

    def upload_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "1")
            server_msg = self.encryptor.receive_encrypted_message(self.client_socket)
            if server_msg:
                messagebox.showinfo("Server", server_msg)
            path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
            if path:
                self.send_image_bytes(path)
                resp = self.encryptor.receive_encrypted_message(self.client_socket)
                if resp:
                    messagebox.showinfo("Result", resp)
            self.refresh_menu()
        except Exception as e:
            messagebox.showerror("Upload error", str(e))
            self.refresh_menu()

    def buy_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "2")
            resp = self.encryptor.receive_encrypted_message(self.client_socket)
            if resp:
                messagebox.showinfo("Buy", resp)
            self.refresh_menu()
        except:
            self.refresh_menu()

    def sell_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "3")
            resp = self.encryptor.receive_encrypted_message(self.client_socket)
            if resp:
                messagebox.showinfo("Sell", resp)
            self.refresh_menu()
        except:
            self.refresh_menu()

    def exit_app(self):
        try:
            if self.client_socket:
                self.encryptor.send_encrypted_message(self.client_socket, "4")
                try:
                    self.client_socket.close()
                except:
                    pass
        except:
            pass
        if self.root:
            self.root.destroy()

    def start(self):
        self.connect_to_server()
        if self.client_socket:
            self.send_client_info()
            self.run_gui()


if __name__ == "__main__":
    Client().start()
