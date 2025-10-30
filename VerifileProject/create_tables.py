from db_manager import DatabaseManager

def create_all_tables(db_manager):
    """
    Create all necessary tables for the application using DatabaseManager instance.

    Args:
        db_manager: An initialized DatabaseManager instance
    """

    # --- Clients Table ---
    db_manager.create_table(
        "clients",
        """(
            user_id INTEGER PRIMARY KEY AUTO_INCREMENT,
            ip TEXT,
            port INTEGER,
            client_username TEXT,
            client_password_hash TEXT,
            email TEXT,
            last_visit DATETIME,
            role TEXT CHECK (role IN ('buyer', 'seller', 'admin'))
        )"""
    )

    # --- Files Table ---
    db_manager.create_table(
        "files",
        """(
            file_id INTEGER PRIMARY KEY AUTO_INCREMENT,
            owner_id INTEGER,
            creator_id INTEGER,
            original_filename TEXT,
            stored_filename TEXT,
            _type TEXT,
            upload_date DATETIME,
            hash_value TEXT,
            signature TEXT,
            stego_file TEXT,
            watermarked_file TEXT,
            price DECIMAL(10,2),
            status TEXT CHECK (status IN ('available', 'sold', 'archived')),
            FOREIGN KEY (owner_id) REFERENCES clients(user_id),
            FOREIGN KEY (creator_id) REFERENCES clients(user_id)
        )"""
    )

    # --- Keys Table ---
    db_manager.create_table(
        "keys_table",
        """(
            key_id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER,
            file_id INTEGER,
            private_key TEXT,
            public_key TEXT,
            created_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES clients(user_id),
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        )"""
    )

    print("✅ All tables created successfully.")
