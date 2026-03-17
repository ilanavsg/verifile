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
            ddos_status BOOLEAN DEFAULT FALSE,
            balance INT DEFAULT 1000,
            role TEXT DEFAULT 'buyer' CHECK (role IN ('buyer', 'seller', 'admin'))
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

    # --- History Table ---
    db_manager.create_table(
    "history_table",
    """(
        key_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        file_id INTEGER,                     
        user_id INTEGER,                      
        action TEXT CHECK (action IN ('sign', 'verify')),  
        hash_value TEXT,                     
        signature TEXT,                      
        verified BOOLEAN,                   
        created_at DATETIME,                 
        FOREIGN KEY (file_id) REFERENCES files(file_id),
        FOREIGN KEY (user_id) REFERENCES clients(user_id)
    )"""
)

print("✅ All tables created successfully.")
