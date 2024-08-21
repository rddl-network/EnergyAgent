import sqlite3

from app.helpers.logs import log, logger


@log
def migrate_smd_store_cid_link_table(cursor):
    """Migrate the smd_store_cid_link table to include the created_at column."""
    try:
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION;")

        # Rename the existing table
        cursor.execute("ALTER TABLE smd_store_cid_link RENAME TO smd_store_cid_link_old;")

        # Create the new table with the updated structure
        cursor.execute(
            """
        CREATE TABLE smd_store_cid_link (
            client_id TEXT,
            cid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (client_id, cid),
            FOREIGN KEY (client_id) REFERENCES smd_store(client_id),
            FOREIGN KEY (cid) REFERENCES key_value_store(cid)
        );
        """
        )

        # Copy data from the old table to the new one
        cursor.execute(
            """
            INSERT INTO smd_store_cid_link (client_id, cid)
            SELECT client_id, cid FROM smd_store_cid_link_old;
        """
        )

        # Drop the old table
        cursor.execute("DROP TABLE smd_store_cid_link_old;")

        # Commit the transaction
        cursor.connection.commit()
        logger.info("Successfully migrated smd_store_cid_link table to include created_at column.")
        return True
    except sqlite3.Error as e:
        # If anything goes wrong, roll back the changes
        cursor.connection.rollback()
        logger.error(f"Failed to migrate smd_store_cid_link table: {e}")
        return False
