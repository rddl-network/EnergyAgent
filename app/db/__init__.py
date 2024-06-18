import sqlite3
import logging

logger = logging.getLogger(__name__)


def create_connection(database_path: str) -> sqlite3.Connection:
    """Create a database connection to the SQLite database"""
    conn = sqlite3.connect(database_path)
    return conn


def init_tables(connection) -> bool:
    """Initialize the tables if they do not exist"""
    if connection:
        cursor = connection.cursor()

        # SQL for creating key_value_store table
        create_key_value_store_table_sql = """
        CREATE TABLE IF NOT EXISTS key_value_store (
            cid TEXT PRIMARY KEY,
            json_value TEXT NOT NULL
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

        # Commit the changes
        connection.commit()


def execute_sql_command(sql_command, params, fetch_data=False):
    from app.dependencies import config

    try:
        cursor = config.db_connection.cursor()
        cursor.execute(sql_command, params)
        if fetch_data:
            return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Failed to carry out SQL command: {e}")
