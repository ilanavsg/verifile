import tkinter as tk

BG = "#0F172A"
CARD = "#1E293B"
PRIMARY = "#38BDF8"
TEXT = "#E5E7EB"
SUBTEXT = "#94A3B8"
BTN = "#38BDF8"
BTN_HOVER = "#0EA5E9"


def run_server_ui():
    root = tk.Tk()
    root.title("VeriFile Server Dashboard")
    root.geometry("750x550")
    root.configure(bg=BG)

    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", pady=20)

    tk.Label(
        header,
        text="VeriFile Server",
        font=("Segoe UI", 26, "bold"),
        fg=PRIMARY,
        bg=BG
    ).pack()

    tk.Label(
        header,
        text="Secure File Verification & Marketplace Platform",
        font=("Segoe UI", 12),
        fg=SUBTEXT,
        bg=BG
    ).pack()

    card = tk.Frame(root, bg=CARD, bd=0, relief="flat")
    card.pack(padx=40, pady=30, fill="both", expand=True)

    tk.Label(
        card,
        text="📁 VeriFile is a secure digital marketplace for verified files.",
        font=("Segoe UI", 14, "bold"),
        bg=CARD,
        fg=TEXT,
        justify="left"
    ).pack(anchor="nw", pady=(10, 10), padx=20)

    content = (
        "What users can do:\n"
        "• Upload images for cryptographic signing\n"
        "• Verify originality using SHA-256 hashing\n"
        "• Buy verified files from other users\n"
        "• Store purchased works securely\n\n"
        "Server protections:\n"
        "• DDoS detection per IP\n"
        "• Automatic IP blocking\n"
        "• Encrypted communication\n"
        "• Duplicate file prevention\n\n"
        "Server Status:\n"
        "• Database: Connected\n"
        "• Encryption: Active\n"
        "• Signature verification: Enabled"
    )

    tk.Label(
        card,
        text=content,
        font=("Segoe UI", 11),
        bg=CARD,
        fg=SUBTEXT,
        justify="left",
        padx=20,
        pady=10
    ).pack(anchor="nw")

    def close_app():
        root.destroy()

    btn_exit = tk.Label(
        card,
        text="Exit",
        bg=BTN,
        fg="white",
        font=("Segoe UI", 12, "bold"),
        width=25,
        height=2,
        cursor="hand2"
    )
    btn_exit.pack(pady=20)
    btn_exit.bind("<Button-1>", lambda e: close_app())
    btn_exit.bind("<Enter>", lambda e: btn_exit.config(bg=BTN_HOVER))
    btn_exit.bind("<Leave>", lambda e: btn_exit.config(bg=BTN))

    root.mainloop()


if __name__ == "__main__":
    run_server_ui()
