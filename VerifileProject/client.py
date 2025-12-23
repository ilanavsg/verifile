import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog, Scrollbar, Canvas, Frame
from tkinter import simpledialog
from constants import IP, PORT, CYAN, GREEN, RED, YELLOW, RESET, BOLD
from encrypt import Encryption
from pathlib import Path
from functools import partial
from io import BytesIO
import base64
from PIL import Image, ImageTk

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
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"{GREEN}Connected to server{RESET}")
            return True
        except Exception as e:
            messagebox.showerror("Connection error", str(e))
            self.client_socket = None
            return False

    def send_client_info(self):
        documents_path = Path.home() / "Documents"
        auth_file = documents_path / "authentication"
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
        self.root.geometry("600x500")
        self.root.config(bg="#fff0f5")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.container = tk.Frame(self.root, bg="#fff0f5")
        self.container.pack(fill="both", expand=True)
        self.pages = {}
        self.pages["main_menu"] = self.create_main_menu(self.container)
        self.pages["buy_page"] = self.create_buy_page(self.container)
        self.pages["storage_page"] = self.create_storage_page(self.container)
        self.show_page("main_menu")
        self.root.mainloop()

    def show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)

    def create_main_menu(self, parent):
        frame = tk.Frame(parent, bg="#fff0f5")
        tk.Label(frame, text=f"Welcome! {self.username}", font=("Arial", 18), bg="#fff0f5", fg="#ff66b2").pack(pady=10)
        self.menu_label = tk.Label(frame, text="", font=("Consolas", 11), bg="#fff0f5", justify="left")
        self.menu_label.pack(pady=5)
        tk.Button(frame, text="Upload", width=28, command=self.upload_action, bg="#ffd1dc").pack(pady=5)
        tk.Button(frame, text="Buy", width=28, command=self.buy_action, bg="#ffe6f0").pack(pady=5)
        tk.Button(frame, text="Sell", width=28, command=self.sell_action, bg="#ffe6f0").pack(pady=5)
        tk.Button(frame, text="My Storage", width=28, command=lambda: self.show_page("storage_page"), bg="#ffe6f0").pack(pady=5)
        tk.Button(frame, text="Exit", width=28, command=self.exit_app, bg="#ffb3cc").pack(pady=15)
        return frame

    def create_buy_page(self, parent):
        frame = tk.Frame(parent, bg="#fff0f5")
        tk.Button(frame, text="Back", command=lambda: self.show_page("main_menu"), bg="#ffd1dc").pack(pady=5)
        canvas = Canvas(frame, bg="#fff0f5")
        scrollbar = Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas, bg="#fff0f5")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        frame.scrollable_frame = scrollable_frame
        return frame

    def create_storage_page(self, parent):
        frame = tk.Frame(parent, bg="#fff0f5")
        tk.Button(frame, text="Back", command=lambda: self.show_page("main_menu"), bg="#ffd1dc").pack(pady=5)
        self.storage_list_frame = tk.Frame(frame, bg="#fff0f5")
        self.storage_list_frame.pack(fill="both", expand=True)
        return frame

    def buy_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "2")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.show_page("buy_page")
        for widget in self.pages["buy_page"].scrollable_frame.winfo_children():
            widget.destroy()
        try:
            images = []
            while True:
                img_name = self.encryptor.receive_encrypted_message(self.client_socket)
                if not img_name:
                    break
                price = self.encryptor.receive_encrypted_message(self.client_socket)
                img_data = self.encryptor.receive_encrypted_message(self.client_socket)
                images.append((img_name, price, img_data))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for idx, (name, price, data) in enumerate(images):
            try:
                img_bytes = BytesIO(base64.b64decode(data))
                pil_img = Image.open(img_bytes).resize((150,150))
                photo = ImageTk.PhotoImage(pil_img)
            except:
                photo = None
            frame = tk.Frame(self.pages["buy_page"].scrollable_frame, bg="#ffe6f0", bd=2, relief="ridge")
            frame.pack(padx=10, pady=10, fill="x")
            if photo:
                tk.Label(frame, image=photo).pack(side="left", padx=10)
                frame.image = photo
            tk.Label(frame, text=f"{name}\nPrice: {price}", bg="#ffe6f0", justify="left").pack(side="left", padx=10)
            tk.Button(frame, text="Buy", bg="#ffd1dc", command=partial(self.confirm_purchase, name, frame)).pack(side="right", padx=10)

    def confirm_purchase(self, image_name, frame_widget):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, f"BUY:{image_name}")
            resp = self.encryptor.receive_encrypted_message(self.client_socket)
            if resp == "SUCCESS":
                messagebox.showinfo("Purchase", f"You bought {image_name}!")
                frame_widget.destroy()
                self.add_to_storage(image_name)
            else:
                messagebox.showerror("Purchase failed", resp)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_to_storage(self, image_name):
        frame = tk.Frame(self.storage_list_frame, bg="#ffe6f0", bd=1, relief="ridge")
        frame.pack(padx=5, pady=5, fill="x")
        tk.Label(frame, text=image_name, bg="#ffe6f0").pack(side="left", padx=10)

    def upload_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "1")
            server_msg = self.encryptor.receive_encrypted_message(self.client_socket)
            if server_msg:
                messagebox.showinfo("Server", server_msg)
            path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
            if not path:
                return
            self.send_image_bytes(path)
            price = simpledialog.askstring(title="Set Price", prompt="Enter price:")
            if not price or not price.replace('.', '', 1).isdigit():
                messagebox.showerror("Invalid price", "Please enter a valid number.")
                return

            self.encryptor.send_encrypted_message(self.client_socket, price)
            resp = self.encryptor.receive_encrypted_message(self.client_socket)
            if resp:
                messagebox.showinfo("Result", resp)
        except Exception as e:
            messagebox.showerror("Upload error", str(e))

    def sell_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "3")
            resp = self.encryptor.receive_encrypted_message(self.client_socket)
            if resp:
                messagebox.showinfo("Sell", resp)
        except Exception as e:
            messagebox.showerror("Sell error", str(e))

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
        if not self.connect_to_server():
            return
        self.send_client_info()
        self.run_gui()

if __name__ == "__main__":
    Client().start()
