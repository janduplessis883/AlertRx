import os
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

class DBManager:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key must be set as environment variables (SUPABASE_URL, SUPABASE_KEY).")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        print("Supabase client initialized.")

    def create_tables_guide(self):
        """
        Guide for creating necessary tables in Supabase.
        Supabase tables are typically created via the Supabase dashboard or migrations.
        This method provides the SQL schema for reference.
        """
        print("\n--- Supabase Table Creation Guide ---")
        print("Please ensure the following tables are created in your Supabase project:")

        print("\n1. Table: 'alerts'")
        print("   Columns:")
        print("     - alert_id (TEXT, PRIMARY KEY)")
        print("     - title (TEXT, NOT NULL)")
        print("     - date_published (TEXT) -- ISO format string")
        print("     - severity (TEXT)")
        print("     - summary (TEXT)")
        print("     - affected_products (TEXT) -- JSON string of a list")
        print("     - recommendations (TEXT) -- JSON string of a list")
        print("     - source_url (TEXT)")
        print("     - source_name (TEXT)")
        print("     - raw_data (TEXT) -- JSON string of a dict")
        print("   Example SQL (run in Supabase SQL Editor):")
        print("""
        CREATE TABLE alerts (
            alert_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date_published TEXT,
            severity TEXT,
            summary TEXT,
            affected_products TEXT,
            recommendations TEXT,
            source_url TEXT,
            source_name TEXT,
            raw_data TEXT
        );
        """)

        print("\n2. Table: 'pharmacist_actions'")
        surgeries = [
            "Scarsdale-Medical-Centre", "Earls-Court-Surgery", "Stanhope-Mews-Surgery",
            "The-Chelsea-Practice", "Health-Partners-at-Violet-Melchett",
            "Emperors-Gate-Health-Centre", "Knightsbridge-Medical-Centre",
            "Earls-Court-Medical-Centre", "The-Abingdon-Medical-Practice",
            "The-Good-Practice", "Royal-Hospital-Chelsea", "Kensington-Park-Medical-Centre"
        ]
        surgery_columns_sql = ",\n".join([f'     - "{s}" INTEGER DEFAULT 0' for s in surgeries])
        print("   Columns:")
        print("     - action_id (SERIAL, PRIMARY KEY)")
        print("     - alert_id (TEXT, NOT NULL)")
        print("     - action_taken (TEXT)")
        print("     - timestamp (TIMESTAMPTZ, DEFAULT NOW())")
        print(surgery_columns_sql)
        print("   Example SQL (run in Supabase SQL Editor):")
        print(f"""
        CREATE TABLE pharmacist_actions (
            action_id SERIAL PRIMARY KEY,
            alert_id TEXT NOT NULL REFERENCES alerts(alert_id),
            action_taken TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            {", ".join([f'"{s}" INTEGER DEFAULT 0' for s in surgeries])}
        );
        """)
        print("\n--- End of Guide ---")

    def insert_alert(self, alert_data: dict):
        """Inserts a single normalized alert into the 'alerts' table in Supabase."""
        try:
            # Convert lists and datetime objects to JSON strings/ISO format for storage
            data_to_insert = alert_data.copy()
            data_to_insert['affected_products'] = str(data_to_insert.get('affected_products', []))
            data_to_insert['recommendations'] = str(data_to_insert.get('recommendations', []))
            data_to_insert['raw_data'] = str(data_to_insert.get('raw_data', {}))
            data_to_insert['date_published'] = data_to_insert['date_published'].isoformat() if pd.notna(data_to_insert['date_published']) else None

            # Supabase upsert (insert or update if alert_id exists)
            response = self.client.table('alerts').upsert(data_to_insert, on_conflict='alert_id').execute()
            # print(f"Alert '{alert_data.get('title')}' inserted/updated successfully: {response.data}")
            return response.data
        except Exception as e:
            print(f"Error inserting alert '{alert_data.get('title')}': {e}")
            return None

    def insert_pharmacist_action(self, action_data: dict):
        """Inserts a pharmacist's action into the 'pharmacist_actions' table in Supabase."""
        try:
            # Prepare data for insertion
            data_to_insert = action_data.copy()
            # Supabase will automatically handle 'timestamp' with DEFAULT NOW()

            response = self.client.table('pharmacist_actions').insert(data_to_insert).execute()
            # print(f"Action for alert '{action_data.get('alert_id')}' recorded successfully: {response.data}")
            return response.data
        except Exception as e:
            print(f"Error inserting pharmacist action for alert '{action_data.get('alert_id')}': {e}")
            return None

    def get_all_alerts(self) -> pd.DataFrame:
        """Retrieves all alerts from the 'alerts' table in Supabase as a pandas DataFrame."""
        try:
            response = self.client.table('alerts').select('*').execute()
            data = response.data
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)

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
        except Exception as e:
            print(f"Error retrieving all alerts: {e}")
            return pd.DataFrame()

    def get_alert_with_actions(self, alert_id: str) -> tuple[dict, pd.DataFrame]:
        """
        Retrieves a specific alert and all associated pharmacist actions from Supabase.
        Returns the alert as a dict and actions as a DataFrame.
        """
        try:
            # Get alert data
            alert_response = self.client.table('alerts').select('*').eq('alert_id', alert_id).limit(1).execute()
            alert_data = alert_response.data[0] if alert_response.data else {}

            if alert_data:
                # Convert back from string to original types
                if 'date_published' in alert_data and alert_data['date_published']:
                    alert_data['date_published'] = pd.to_datetime(alert_data['date_published'])
                if 'affected_products' in alert_data and alert_data['affected_products']:
                    alert_data['affected_products'] = eval(alert_data['affected_products'])
                if 'recommendations' in alert_data and alert_data['recommendations']:
                    alert_data['recommendations'] = eval(alert_data['recommendations'])
                if 'raw_data' in alert_data and alert_data['raw_data']:
                    alert_data['raw_data'] = eval(alert_data['raw_data'])

            # Get actions data
            actions_response = self.client.table('pharmacist_actions').select('*').eq('alert_id', alert_id).execute()
            actions_data = actions_response.data
            actions_df = pd.DataFrame(actions_data) if actions_data else pd.DataFrame()

            if 'timestamp' in actions_df.columns:
                actions_df['timestamp'] = pd.to_datetime(actions_df['timestamp'])

            return alert_data, actions_df
        except Exception as e:
            print(f"Error retrieving alert '{alert_id}' with actions: {e}")
            return {}, pd.DataFrame()

if __name__ == "__main__":
    # Example usage (requires SUPABASE_URL and SUPABASE_KEY environment variables)
    # For local testing, you might need to mock Supabase client or set up a test project.
    # Ensure you have created the 'alerts' and 'pharmacist_actions' tables in your Supabase project
    # as per the guide in create_tables_guide() before running this example.

    # Set dummy environment variables for local testing if not already set
    # os.environ["SUPABASE_URL"] = "YOUR_SUPABASE_URL"
    # os.environ["SUPABASE_KEY"] = "YOUR_SUPABASE_ANON_KEY"

    try:
        db_manager = DBManager()
        db_manager.create_tables_guide() # Just prints the guide, doesn't create tables

        # Example: Insert a sample alert
        sample_alert = {
            "alert_id": "TEST-SUPABASE-001",
            "title": "Supabase Test Alert 1",
            "date_published": datetime(2023, 4, 1),
            "severity": "Medium",
            "summary": "This is a test alert for Supabase integration.",
            "affected_products": ["Supabase Product A", "Supabase Product B"],
            "recommendations": ["Check Supabase docs", "Enjoy the backend"],
            "source_url": "http://supabase.com/test1",
            "source_name": "Supabase Test Source",
            "raw_data": {"original_supabase_field": "value"}
        }
        # Uncomment to insert:
        # db_manager.insert_alert(sample_alert)

        # Example: Insert a sample pharmacist action
        sample_action = {
            "alert_id": "TEST-SUPABASE-001",
            "action_taken": "Configured Supabase client.",
            "Scarsdale-Medical-Centre": 1,
            "Earls-Court-Surgery": 2
        }
        # Uncomment to insert:
        # db_manager.insert_pharmacist_action(sample_action)

        print("\nAttempting to retrieve all alerts (requires data in Supabase):")
        all_alerts_df = db_manager.get_all_alerts()
        print(all_alerts_df)

        print("\nAttempting to retrieve alert TEST-SUPABASE-001 with actions:")
        alert_data, actions_df = db_manager.get_alert_with_actions("TEST-SUPABASE-001")
        print("Alert Data:", alert_data)
        print("Actions Data:")
        print(actions_df)

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An error occurred during Supabase example usage: {e}")
