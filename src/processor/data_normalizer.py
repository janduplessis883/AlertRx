import pandas as pd

# Define the common schema for medical alerts
# This schema should be comprehensive enough to capture all relevant information
# from various sources.
MEDICAL_ALERT_SCHEMA = {
    "alert_id": str,
    "title": str,
    "date_published": "datetime64[ns]", # Use pandas datetime type
    "severity": str, # e.g., "High", "Medium", "Low"
    "summary": str,
    "affected_products": list, # List of strings
    "recommendations": list, # List of strings
    "source_url": str,
    "source_name": str,
    "raw_data": dict # Store the original Firecrawl JSON for debugging/future use
}

def normalize_alert_data(raw_alert_data: dict) -> dict:
    """
    Normalizes a single raw medical alert data dictionary into the common schema.

    Args:
        raw_alert_data (dict): The raw data extracted by Firecrawl and parsed by source-specific functions.

    Returns:
        dict: A dictionary conforming to the MEDICAL_ALERT_SCHEMA.
    """
    normalized_data = {
        "alert_id": raw_alert_data.get("alert_id", ""),
        "title": raw_alert_data.get("title", ""),
        "date_published": pd.to_datetime(raw_alert_data.get("date_published"), errors='coerce'),
        "severity": raw_alert_data.get("severity", "Medium"),
        "summary": raw_alert_data.get("summary", ""),
        "affected_products": raw_alert_data.get("affected_products", []),
        "recommendations": raw_alert_data.get("recommendations", []),
        "source_url": raw_alert_data.get("source_url", ""),
        "source_name": raw_alert_data.get("source_name", ""),
        "raw_data": raw_alert_data # Store the original for reference
    }
    return normalized_data

def process_alerts_to_dataframe(list_of_raw_alerts: list) -> pd.DataFrame:
    """
    Processes a list of raw alert dictionaries and returns a pandas DataFrame.

    Args:
        list_of_raw_alerts (list): A list of dictionaries, each representing a raw alert.

    Returns:
        pd.DataFrame: A DataFrame where each row is a normalized medical alert.
    """
    normalized_alerts = [normalize_alert_data(alert) for alert in list_of_raw_alerts]
    df = pd.DataFrame(normalized_alerts)

    # Ensure correct data types
    for col, dtype in MEDICAL_ALERT_SCHEMA.items():
        if col in df.columns:
            if str(dtype).startswith("datetime"):
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif dtype == list:
                # Ensure list type, handle non-list inputs gracefully
                df[col] = df[col].apply(lambda x: x if isinstance(x, list) else [x] if x is not None else [])
            else:
                df[col] = df[col].astype(dtype, errors='ignore')
    return df

if __name__ == "__main__":
    # Example usage
    sample_raw_alert = {
        "alert_id": "GOVUK-2023-001",
        "title": "Important Drug Safety Update: XYZ Drug",
        "date_published": "2023-01-15",
        "content": "This is a summary of the alert...",
        "source_url": "https://www.gov.uk/drug-safety-update/xyz-drug",
        "source_name": "GOV.UK Drug Safety Update",
        "severity": "High",
        "affected_products": ["XYZ Drug 10mg", "XYZ Drug 20mg"],
        "recommendations": ["Monitor patients closely", "Adjust dosage"]
    }

    normalized_alert = normalize_alert_data(sample_raw_alert)
    print("Normalized Alert:")
    print(normalized_alert)

    sample_raw_alerts_list = [
        sample_raw_alert,
        {
            "alert_id": "ANOTHER-2023-005",
            "title": "Recall: ABC Medical Device",
            "date_published": "2023-02-01",
            "content": "Details about the recall...",
            "source_url": "https://example.com/alerts/abc-device",
            "source_name": "Another Medical Alert Source",
            "severity": "Medium",
            "affected_products": ["ABC Device Model X"],
            "recommendations": ["Cease use immediately"]
        }
    ]

    alerts_df = process_alerts_to_dataframe(sample_raw_alerts_list)
    print("\nAlerts DataFrame:")
    print(alerts_df)
    print("\nDataFrame Info:")
    alerts_df.info()
