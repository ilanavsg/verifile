import io
import socket
import os
import threading
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
from gui import create_main_menu, create_buy_page, create_storage_page
import json


class Client:
    def __init__(self):
        self.host = IP
        self.port = PORT
        self.client_socket = None
        self.encryptor = Encryption()
        self.root = None
        self.username = ""
        self.client_id = None
        self.storage_list_frame = None
        self.my_works = []

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
        resp2 = self.encryptor.receive_encrypted_message(self.client_socket)
        if resp2:
            self.client_id = int(resp2)
        resp3 = self.encryptor.receive_encrypted_message(self.client_socket)
        print(resp3)
        if resp3.startswith("WORKS:"):
            cmd, data = resp3.split(":", 1)
            self.my_works = json.loads(data)

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
        self.pages["main_menu"] = create_main_menu(self, self.container)
        self.pages["buy_page"] = create_buy_page(self, self.container)
        self.pages["storage_page"] = create_storage_page(self, self.container)
        self.show_page("main_menu")
        self.root.mainloop()

    def show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)
        if page_name == "storage_page":
            self.render_storage()

    def render_storage(self):
        if not self.storage_list_frame:
            return

        for widget in self.storage_list_frame.winfo_children():
            widget.destroy()

        for work in self.my_works:
            item = tk.Frame(
                self.storage_list_frame,
                bg="#ffe6f0",
                bd=1,
                relief="ridge"
            )
            item.pack(padx=5, pady=5, fill="x")

            tk.Label(
                item,
                text=work,
                bg="#ffe6f0"
            ).pack(side="left", padx=10)

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
            resp1 = self.encryptor.receive_encrypted_message(self.client_socket)
            if resp1:
                messagebox.showinfo("Result", resp1)

        except Exception as e:
            messagebox.showerror("Upload error", str(e))

    def buy_action(self):
        try:
            # Request buy list from server
            self.encryptor.send_encrypted_message(self.client_socket, "2")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.show_page("buy_page")

        # Clear old widgets
        for widget in self.pages["buy_page"].scrollable_frame.winfo_children():
            widget.destroy()

        images = []
        try:
            # Receive all images info (name, price, base64 data)
            while True:
                img_name = self.encryptor.receive_encrypted_message(self.client_socket)
                if not img_name:
                    break
                price = self.encryptor.receive_encrypted_message(self.client_socket)
                img_data = self.encryptor.receive_encrypted_message(self.client_socket)
                if img_name is None or price is None or img_data is None:
                    break
                images.append((img_name, price, img_data))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # Render images as thumbnails
        for name, price, data in images:
            frame = tk.Frame(self.pages["buy_page"].scrollable_frame, bg="#ffe6f0", bd=2, relief="ridge")
            frame.pack(padx=10, pady=10, fill="x")

            # Thumbnail image
            photo = None
            if data:
                try:
                    with BytesIO(base64.b64decode(data)) as img_bytes:
                        pil_img = Image.open(img_bytes)
                        pil_img.thumbnail((150, 150))
                        photo = ImageTk.PhotoImage(pil_img)
                except Exception:
                    photo = None

            if photo:
                lbl_img = tk.Label(frame, image=photo)
                lbl_img.image = photo  # keep reference per widget
                lbl_img.pack(side="left", padx=10)

            tk.Label(frame, text=f"{name}\nPrice: {price}", bg="#ffe6f0", justify="left").pack(side="left", padx=10)

            tk.Button(
                frame,
                text="Buy",
                bg="#ffd1dc",
                command=partial(self.confirm_purchase, name, frame)
            ).pack(side="right", padx=10)

    def confirm_purchase(self, image_name, frame_widget):
        try:
            # Send purchase request
            self.encryptor.send_encrypted_message(self.client_socket, f"BUY:{image_name}")
            resp = self.encryptor.receive_encrypted_message(self.client_socket)

            if resp != "SUCCESS":
                messagebox.showerror("Purchase failed", resp)
                return

            # Receive filename and size
            info = self.encryptor.receive_encrypted_message(self.client_socket)
            filename, filesize = info.split("|")
            filesize = int(filesize)

            self.encryptor.send_encrypted_message(self.client_socket, "READY")

            out_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)

            received_bytes = b""
            while len(received_bytes) < filesize:
                chunk = self.client_socket.recv(min(4096, filesize - len(received_bytes)))
                if not chunk:
                    break
                received_bytes += chunk

            if len(received_bytes) == filesize:
                with open(out_path, "wb") as f:
                    f.write(received_bytes)
                print("File received successfully")
            else:
                print("File incomplete or failed")

            messagebox.showinfo("Purchase", f"You bought {image_name}!\nSaved to Desktop.")
            frame_widget.destroy()
            self.render_storage()  # refresh storage page

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def sell_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "3")
            cmd = self.encryptor.receive_encrypted_message(self.client_socket)

            if cmd != "SEND_IMAGE":
                return

            path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *jpeg")])
            if not path:
                return

            filename = os.path.basename(path)
            data = open(path, "rb").read()
            price = simpledialog.askstring("Sell Image", "Enter price:")
            if not price:
                return
            
            self.encryptor.send_encrypted_message(self.client_socket, filename)
            self.encryptor.send_encrypted_message(self.client_socket, str(len(data)))
            self.encryptor.receive_encrypted_message(self.client_socket)
            self.client_socket.sendall(data)
            self.encryptor.send_encrypted_message(self.client_socket, price)
            result = self.encryptor.receive_encrypted_message(self.client_socket)
            msg = self.encryptor.receive_encrypted_message(self.client_socket)

            if result == "SUCCESS":
                messagebox.showinfo("Sell Result", msg)
            else:
                messagebox.showerror("Sell Error", msg)

        except Exception as e:
            messagebox.showerror("Sell error", str(e))

    def verify_action(self):
        try:
            self.encryptor.send_encrypted_message(self.client_socket, "4")

            cmd = self.encryptor.receive_encrypted_message(self.client_socket)
            print(cmd)
            if cmd != "SEND_IMAGE":
                return

            path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg")])
            if not path:
                return

            data = open(path, "rb").read()

            self.encryptor.send_encrypted_message(
                self.client_socket, os.path.basename(path)
            )
            self.encryptor.send_encrypted_message(
                self.client_socket, str(len(data))
            )

            self.encryptor.receive_encrypted_message(self.client_socket)
            self.client_socket.sendall(data)

            result = self.encryptor.receive_encrypted_message(self.client_socket)
            msg = self.encryptor.receive_encrypted_message(self.client_socket)

            if result == "VALID":
                messagebox.showinfo("Verify Result", f"✅ {msg}")
            else:
                messagebox.showerror("Verify Result", f"❌ {msg}")

        except Exception as e:
            messagebox.showerror("Verify error", str(e))

    def exit_app(self):
        try:
            if self.client_socket:
                self.encryptor.send_encrypted_message(self.client_socket, "5")
                try:
                    self.encryptor.receive_encrypted_message(self.client_socket)
                except:
                    pass

                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.client_socket.close()
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
