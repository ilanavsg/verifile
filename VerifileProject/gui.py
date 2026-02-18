import tkinter as tk
from functools import partial
from PIL import Image, ImageTk
from io import BytesIO
import base64
import customtkinter as ctk


PRIMARY = "#A5B4FC"
ACCENT = "#C7D2FE"
BG = "#F3F4F6"
CARD = "#FFFFFF"
TEXT = "#111827"
SUBTEXT = "#6B7280"
BTN_BG = PRIMARY
BTN_HOVER = ACCENT
EXIT_BG = "#FECACA"
EXIT_HOVER = "#FCA5A5"

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


def create_main_menu(client, parent):
    main_frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
    main_frame.pack(fill="both", expand=True)

    header_frame = ctk.CTkFrame(main_frame, fg_color="#A0D8FF", height=80, corner_radius=0)
    header_frame.pack(fill="x")

    ctk.CTkLabel(
        header_frame,
        text="VeriFile",
        font=("Segoe UI", 26, "bold"),
        text_color=TEXT,
        fg_color="#A0D8FF"
    ).place(x=20, y=15)

    ctk.CTkLabel(
        header_frame,
        text="Secure digital marketplace for verified files",
        font=("Segoe UI", 12),
        text_color=SUBTEXT,
        fg_color="#A0D8FF"
    ).place(x=20, y=50)

    card = ctk.CTkFrame(main_frame, fg_color=CARD, corner_radius=20)
    card.pack(fill="x", pady=40, padx=40)

    ctk.CTkLabel(
        card,
        text=f"Welcome {client.username}!",
        font=("Segoe UI", 20, "bold"),
        text_color=TEXT
    ).pack(pady=(20, 10), padx=20, anchor="w")

    ctk.CTkLabel(
        card,
        text="What would you like to do today?",
        font=("Segoe UI", 14),
        text_color=SUBTEXT
    ).pack(pady=(0, 20), padx=20, anchor="w")

    btn_frame = ctk.CTkFrame(card, fg_color=CARD)
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))

    def create_button(text, command, color=BTN_BG, hover_color=BTN_HOVER):
        btn = ctk.CTkButton(
            btn_frame,
            text=text,
            command=command,
            corner_radius=12,
            fg_color=color,
            hover_color=hover_color,
            text_color=TEXT,
            font=("Segoe UI", 11, "bold"),
            height=30
        )
        btn.pack(pady=4, fill="x")

        return btn

    create_button("Upload", client.upload_action)
    create_button("Buy", client.buy_action)
    create_button("Sell", client.sell_action)
    create_button("Verify", client.verify_action)
    create_button("My Storage", lambda: client.show_page("storage_page"))
    create_button("Exit", client.exit_app, color=EXIT_BG, hover_color=EXIT_HOVER)

    return main_frame


def create_buy_page(client, parent):
    frame = ctk.CTkFrame(parent, fg_color=BG)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    back_btn = ctk.CTkButton(frame, text="Back", command=lambda: client.show_page("main_menu"),
                             fg_color=BTN_BG, hover_color=BTN_HOVER)
    back_btn.pack(pady=10)

    # Scrollable area
    canvas_container = ctk.CTkFrame(frame, fg_color=BG)
    canvas_container.pack(fill="both", expand=True)

    canvas = tk.Canvas(canvas_container, bg=BG)
    scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = tk.Frame(canvas, bg=BG)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_frame_configure)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    frame.scrollable_frame = scrollable_frame
    return frame


def create_storage_page(client, parent):
    frame = ctk.CTkFrame(parent, fg_color=BG)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    back_btn = ctk.CTkButton(frame, text="Back", command=lambda: client.show_page("main_menu"),
                             fg_color=BTN_BG, hover_color=BTN_HOVER)
    back_btn.pack(pady=10)

    client.storage_list_frame = ctk.CTkFrame(frame, fg_color=BG)
    client.storage_list_frame.pack(fill="both", expand=True)

    return frame


def add_buy_item(container, name, price, img_data, buy_callback):
    item = ctk.CTkFrame(container, fg_color="#FFE6F0", corner_radius=10)
    item.pack(padx=10, pady=10, fill="x")

    try:
        img_bytes = BytesIO(base64.b64decode(img_data))
        pil_img = Image.open(img_bytes).resize((150, 150))
        photo = ImageTk.PhotoImage(pil_img)

        img_label = ctk.CTkLabel(item, image=photo, fg_color="#FFE6F0")
        img_label.image = photo
        img_label.pack(side="left", padx=10)
    except:
        pass

    ctk.CTkLabel(
        item,
        text=f"{name}\nPrice: {price}",
        fg_color="#FFE6F0",
        justify="left"
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        item,
        text="Buy",
        fg_color="#FFD1DC",
        hover_color="#FFC0D9",
        command=partial(buy_callback, name, item)
    ).pack(side="right", padx=10)
