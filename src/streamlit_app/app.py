import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database.db_manager import DBManager
# from src.scraper.firecrawl_scraper import FirecrawlScraper # Will be used later
# from src.processor.data_normalizer import process_alerts_to_dataframe # Will be used later

# List of surgeries provided by the user
SURGERIES = [
    "Scarsdale-Medical-Centre", "Earls-Court-Surgery", "Stanhope-Mews-Surgery",
    "The-Chelsea-Practice", "Health-Partners-at-Violet-Melchett",
    "Emperors-Gate-Health-Centre", "Knightsbridge-Medical-Centre",
    "Earls-Court-Medical-Centre", "The-Abingdon-Medical-Practice",
    "The-Good-Practice", "Royal-Hospital-Chelsea", "Kensington-Park-Medical-Centre"
]

def main():
    st.set_page_config(layout="wide", page_title="AlertRx - Medical Alert Management")
    st.title("💊 AlertRx: Medical Alert Management System")

    db_manager = DBManager()
    db_manager.connect()
    db_manager.create_tables() # Ensure tables exist

    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["View Alerts", "Enter Actions"])

    if page == "View Alerts":
        view_alerts_page(db_manager)
    elif page == "Enter Actions":
        enter_actions_page(db_manager)

    db_manager.close()

def view_alerts_page(db_manager: DBManager):
    st.header("Current Medical Alerts")

    alerts_df = db_manager.get_all_alerts()

    if alerts_df.empty:
        st.info("No medical alerts found in the database. Please run the scraper to fetch alerts.")
        return

    # Display alerts in a table
    st.dataframe(alerts_df[['title', 'date_published', 'severity', 'source_name', 'source_url']], use_container_width=True)

    st.subheader("Alert Details")
    selected_alert_title = st.selectbox("Select an alert to view details:", alerts_df['title'].tolist())

    if selected_alert_title:
        selected_alert = alerts_df[alerts_df['title'] == selected_alert_title].iloc[0].to_dict()
        st.write(f"**Title:** {selected_alert['title']}")
        st.write(f"**Date Published:** {selected_alert['date_published'].strftime('%Y-%m-%d') if pd.notna(selected_alert['date_published']) else 'N/A'}")
        st.write(f"**Severity:** {selected_alert['severity']}")
        st.write(f"**Source:** [{selected_alert['source_name']}]({selected_alert['source_url']})")
        st.write(f"**Summary:** {selected_alert['summary']}")
        st.write(f"**Affected Products:** {', '.join(selected_alert['affected_products'])}")
        st.write(f"**Recommendations:** {', '.join(selected_alert['recommendations'])}")

        st.subheader("Actions Taken for this Alert")
        alert_data, actions_df = db_manager.get_alert_with_actions(selected_alert['alert_id'])
        if actions_df.empty:
            st.info("No actions recorded for this alert yet.")
        else:
            st.dataframe(actions_df[['timestamp', 'action_taken'] + SURGERIES], use_container_width=True)


def enter_actions_page(db_manager: DBManager):
    st.header("Enter Actions for an Alert")

    alerts_df = db_manager.get_all_alerts()
    if alerts_df.empty:
        st.warning("No alerts available to enter actions for. Please fetch alerts first.")
        return

    selected_alert_title = st.selectbox("Select an alert to record actions:", alerts_df['title'].tolist())

    if selected_alert_title:
        selected_alert = alerts_df[alerts_df['title'] == selected_alert_title].iloc[0].to_dict()
        st.write(f"**Selected Alert:** {selected_alert['title']}")
        st.write(f"**Summary:** {selected_alert['summary']}")

        with st.form("pharmacist_action_form"):
            action_taken = st.text_area("Actions Taken:", help="Describe the actions taken in response to this alert.")

            st.subheader("Patients Affected per Surgery")
            surgery_patient_counts = {}
            cols = st.columns(3) # Display in 3 columns for better layout
            for i, surgery in enumerate(SURGERIES):
                with cols[i % 3]:
                    surgery_patient_counts[surgery] = st.number_input(
                        f"Patients in {surgery}:",
                        min_value=0,
                        value=0,
                        step=1,
                        key=f"patients_{surgery}"
                    )

            submitted = st.form_submit_button("Submit Actions")

            if submitted:
                if not action_taken:
                    st.error("Please describe the actions taken.")
                else:
                    action_data = {
                        "alert_id": selected_alert['alert_id'],
                        "action_taken": action_taken,
                        **surgery_patient_counts # Unpack surgery counts
                    }
                    db_manager.insert_pharmacist_action(action_data)
                    st.success("Actions recorded successfully!")
                    st.rerun() # Rerun to clear form and update display

if __name__ == "__main__":
    main()
