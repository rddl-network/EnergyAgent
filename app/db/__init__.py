import sqlite3
from threading import Lock

from app.db.migrations.add_created_at_to_smd_link import migrate_smd_store_cid_link_table
from app.helpers.logs import log, logger


@log
def create_connection(database_path: str) -> sqlite3.Connection:
    """Create a database connection to the SQLite database"""
    conn = sqlite3.connect(database_path)
    return conn


@log
def init_tables(connection) -> bool:
    """Initialize the tables if they do not exist"""
    if connection:
        cursor = connection.cursor()

        create_key_value_store_table_sql = """
        CREATE TABLE IF NOT EXISTS key_value_store (
            cid TEXT PRIMARY KEY,
            json_value TEXT NOT NULL
        );
        """

        create_smd_store_table_sql = """
        CREATE TABLE IF NOT EXISTS smd_store (
            client_id TEXT PRIMARY KEY
        );
        """

        create_smd_store_cid_link_table_sql = """
        CREATE TABLE IF NOT EXISTS smd_store_cid_link (
            client_id TEXT,
            cid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (client_id, cid),
            FOREIGN KEY (client_id) REFERENCES smd_store(client_id),
            FOREIGN KEY (cid) REFERENCES key_value_store(cid)
        );
        """

        # SQL for creating transactions table
        create_transactions_table_sql = """
        CREATE TABLE IF NOT EXISTS transactions (
            txhash TEXT NOT NULL,
            cid TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # SQL for creating activity timeline
        create_activity_timeline_table_sql = """
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            txhash TEXT,
            command TEXT,
            result TEXT NOT NULL,
            context TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Execute SQL statements
        cursor.execute(create_key_value_store_table_sql)
        cursor.execute(create_transactions_table_sql)
        cursor.execute(create_activity_timeline_table_sql)
        cursor.execute(create_smd_store_table_sql)
        cursor.execute(create_smd_store_cid_link_table_sql)

        # Check if smd_store_cid_link table exists and has the correct structure
        cursor.execute("PRAGMA table_info(smd_store_cid_link);")
        columns = {row[1] for row in cursor.fetchall()}

        if "created_at" not in columns:
            # Perform migration to add created_at column while preserving data
            migration_success = migrate_smd_store_cid_link_table(cursor)
            if not migration_success:
                logger.error("Failed to migrate smd_store_cid_link table.")
                return False
        else:
            logger.info("smd_store_cid_link table already has the correct structure.")
        # Commit the changes
        connection.commit()


lock = Lock()


@log
def execute_sql_command(sql_command, params, fetch_data=False):
    from app.dependencies import config

    global lock
    try:
        with lock:
            cursor = config.db_connection.cursor()
            cursor.execute(sql_command, params)
            if fetch_data:
                result = cursor.fetchall()
            else:
                config.db_connection.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to carry out SQL command: {e}")
        raise
    finally:
        cursor.close()
    if fetch_data:
        return result
