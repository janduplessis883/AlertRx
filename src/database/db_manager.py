import sqlite3
import pandas as pd
from datetime import datetime

DATABASE_PATH = "data/alerts.db"

class DBManager:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establishes a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Allows accessing columns by name
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            self.conn = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")
            self.conn = None

    def create_tables(self):
        """Creates the necessary tables if they don't exist."""
        if not self.conn:
            self.connect()
        if not self.conn:
            print("Cannot create tables: No database connection.")
            return

        cursor = self.conn.cursor()

        # Table for medical alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date_published TEXT, -- Stored as ISO format string
                severity TEXT,
                summary TEXT,
                affected_products TEXT, -- Stored as JSON string
                recommendations TEXT, -- Stored as JSON string
                source_url TEXT,
                source_name TEXT,
                raw_data TEXT -- Stored as JSON string
            )
        """)

        # Table for pharmacist actions
        # The surgeries list is fixed, so we can create columns for each
        surgeries = [
            "Scarsdale-Medical-Centre", "Earls-Court-Surgery", "Stanhope-Mews-Surgery",
            "The-Chelsea-Practice", "Health-Partners-at-Violet-Melchett",
            "Emperors-Gate-Health-Centre", "Knightsbridge-Medical-Centre",
            "Earls-Court-Medical-Centre", "The-Abingdon-Medical-Practice",
            "The-Good-Practice", "Royal-Hospital-Chelsea", "Kensington-Park-Medical-Centre"
        ]
        surgery_columns = ", ".join([f'"{s}" INTEGER DEFAULT 0' for s in surgeries])

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS pharmacist_actions (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                action_taken TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                {surgery_columns},
                FOREIGN KEY (alert_id) REFERENCES alerts (alert_id)
            )
        """)
        self.conn.commit()
        print("Tables created successfully or already exist.")

    def insert_alert(self, alert_data: dict):
        """Inserts a single normalized alert into the 'alerts' table."""
        if not self.conn:
            self.connect()
        if not self.conn:
            print("Cannot insert alert: No database connection.")
            return

        cursor = self.conn.cursor()
        try:
            # Convert lists and dicts to JSON strings for storage
            alert_data['affected_products'] = str(alert_data.get('affected_products', []))
            alert_data['recommendations'] = str(alert_data.get('recommendations', []))
            alert_data['raw_data'] = str(alert_data.get('raw_data', {}))
            alert_data['date_published'] = alert_data['date_published'].isoformat() if pd.notna(alert_data['date_published']) else None

            cursor.execute("""
                INSERT OR REPLACE INTO alerts (
                    alert_id, title, date_published, severity, summary,
                    affected_products, recommendations, source_url, source_name, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_data.get('alert_id'),
                alert_data.get('title'),
                alert_data.get('date_published'),
                alert_data.get('severity'),
                alert_data.get('summary'),
                alert_data.get('affected_products'),
                alert_data.get('recommendations'),
                alert_data.get('source_url'),
                alert_data.get('source_name'),
                alert_data.get('raw_data')
            ))
            self.conn.commit()
            # print(f"Alert '{alert_data.get('title')}' inserted/updated successfully.")
        except sqlite3.Error as e:
            print(f"Error inserting alert '{alert_data.get('title')}': {e}")

    def insert_pharmacist_action(self, action_data: dict):
        """Inserts a pharmacist's action into the 'pharmacist_actions' table."""
        if not self.conn:
            self.connect()
        if not self.conn:
            print("Cannot insert action: No database connection.")
            return

        cursor = self.conn.cursor()
        try:
            # Prepare columns and values dynamically for surgery counts
            surgeries = [
                "Scarsdale-Medical-Centre", "Earls-Court-Surgery", "Stanhope-Mews-Surgery",
                "The-Chelsea-Practice", "Health-Partners-at-Violet-Melchett",
                "Emperors-Gate-Health-Centre", "Knightsbridge-Medical-Centre",
                "Earls-Court-Medical-Centre", "The-Abingdon-Medical-Practice",
                "The-Good-Practice", "Royal-Hospital-Chelsea", "Kensington-Park-Medical-Centre"
            ]

            cols = ["alert_id", "action_taken"] + [s for s in surgeries]
            values = [action_data.get("alert_id"), action_data.get("action_taken")] + \
                     [action_data.get(s, 0) for s in surgeries]

            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join([f'"{c}"' for c in cols]) # Quote column names for safety

            cursor.execute(f"""
                INSERT INTO pharmacist_actions ({col_names})
                VALUES ({placeholders})
            """, values)
            self.conn.commit()
            # print(f"Action for alert '{action_data.get('alert_id')}' recorded successfully.")
        except sqlite3.Error as e:
            print(f"Error inserting pharmacist action for alert '{action_data.get('alert_id')}': {e}")

    def get_all_alerts(self) -> pd.DataFrame:
        """Retrieves all alerts from the 'alerts' table as a pandas DataFrame."""
        if not self.conn:
            self.connect()
        if not self.conn:
            print("Cannot retrieve alerts: No database connection.")
            return pd.DataFrame()

        query = "SELECT * FROM alerts"
        df = pd.read_sql_query(query, self.conn)

        # Convert relevant columns back from string to their original types
        if 'date_published' in df.columns:
            df['date_published'] = pd.to_datetime(df['date_published'], errors='coerce')
        if 'affected_products' in df.columns:
            df['affected_products'] = df['affected_products'].apply(eval) # eval to convert string back to list
        if 'recommendations' in df.columns:
            df['recommendations'] = df['recommendations'].apply(eval)
        if 'raw_data' in df.columns:
            df['raw_data'] = df['raw_data'].apply(eval) # eval to convert string back to dict

        return df

    def get_alert_with_actions(self, alert_id: str) -> tuple[dict, pd.DataFrame]:
        """
        Retrieves a specific alert and all associated pharmacist actions.
        Returns the alert as a dict and actions as a DataFrame.
        """
        if not self.conn:
            self.connect()
        if not self.conn:
            print("Cannot retrieve alert with actions: No database connection.")
            return {}, pd.DataFrame()

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
        alert_row = cursor.fetchone()

        alert_data = {}
        if alert_row:
            alert_data = dict(alert_row)
            # Convert back from string to original types
            if 'date_published' in alert_data and alert_data['date_published']:
                alert_data['date_published'] = pd.to_datetime(alert_data['date_published'])
            if 'affected_products' in alert_data and alert_data['affected_products']:
                alert_data['affected_products'] = eval(alert_data['affected_products'])
            if 'recommendations' in alert_data and alert_data['recommendations']:
                alert_data['recommendations'] = eval(alert_data['recommendations'])
            if 'raw_data' in alert_data and alert_data['raw_data']:
                alert_data['raw_data'] = eval(alert_data['raw_data'])

        actions_df = pd.DataFrame()
        if alert_data:
            query = "SELECT * FROM pharmacist_actions WHERE alert_id = ?"
            actions_df = pd.read_sql_query(query, self.conn, params=(alert_id,))
            if 'timestamp' in actions_df.columns:
                actions_df['timestamp'] = pd.to_datetime(actions_df['timestamp'])

        return alert_data, actions_df

if __name__ == "__main__":
    # Example usage
    db_manager = DBManager()
    db_manager.connect()
    db_manager.create_tables()

    # Sample alert data (should come from data_normalizer)
    sample_alert = {
        "alert_id": "TEST-001",
        "title": "Test Alert 1",
        "date_published": datetime(2023, 3, 10),
        "severity": "Low",
        "summary": "This is a test alert summary.",
        "affected_products": ["Product A", "Product B"],
        "recommendations": ["Recommendation 1", "Recommendation 2"],
        "source_url": "http://test.com/alert1",
        "source_name": "Test Source",
        "raw_data": {"original_field": "value"}
    }
    db_manager.insert_alert(sample_alert)

    sample_alert_2 = {
        "alert_id": "TEST-002",
        "title": "Test Alert 2",
        "date_published": datetime(2023, 3, 15),
        "severity": "High",
        "summary": "Another test alert summary.",
        "affected_products": ["Product C"],
        "recommendations": ["Recommendation 3"],
        "source_url": "http://test.com/alert2",
        "source_name": "Test Source",
        "raw_data": {"original_field_2": "value_2"}
    }
    db_manager.insert_alert(sample_alert_2)

    # Sample pharmacist action data
    sample_action = {
        "alert_id": "TEST-001",
        "action_taken": "Reviewed and communicated to staff.",
        "Scarsdale-Medical-Centre": 5,
        "Earls-Court-Surgery": 3,
        "The-Chelsea-Practice": 10
    }
    db_manager.insert_pharmacist_action(sample_action)

    sample_action_2 = {
        "alert_id": "TEST-001",
        "action_taken": "Follow-up action: updated patient records.",
        "Scarsdale-Medical-Centre": 2,
        "Emperors-Gate-Health-Centre": 7
    }
    db_manager.insert_pharmacist_action(sample_action_2)

    print("\nAll Alerts:")
    all_alerts_df = db_manager.get_all_alerts()
    print(all_alerts_df)

    print("\nAlert TEST-001 with Actions:")
    alert_1_data, alert_1_actions_df = db_manager.get_alert_with_actions("TEST-001")
    print("Alert Data:", alert_1_data)
    print("Actions Data:")
    print(alert_1_actions_df)

    db_manager.close()
