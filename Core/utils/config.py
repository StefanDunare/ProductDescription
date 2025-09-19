import os

class Config:
    """
    Loads and validates all required environment variables for the application.
    It raises a clear error if any variable is missing.
    """
    def __init__(self):
        # Define all the required environment variable keys in one place.
        self.required_vars = [
            "GOOGLE_API_KEY",
            "GEMINI_MODEL",
            "API_KEY",
            "SEARCH_ENGINE_ID",
            "SQL_CONN_STRING"
        ]
        
        # --- Load and Validate ---
        self.load_and_validate()
        
        # --- Store the validated variables as class attributes ---
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL")
        self.api_key = os.getenv("API_KEY")
        self.search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        self.sql_conn_string = os.getenv("SQL_CONN_STRING")
        
        print("Configuration loaded and validated successfully...",end='')

    def load_and_validate(self):
        """
        Checks for the existence of all required environment variables.
        """
        missing_vars = [var for var in self.required_vars if not os.getenv(var)]
        
        if missing_vars:
            # If any variables are missing, raise a single, comprehensive error.
            raise ValueError(
                f"CRITICAL ERROR: The following required environment variables are not set: {', '.join(missing_vars)}. "
                "Please create a .env file and set them."
            )

# Create a global instance of the config to be imported by other modules.
try:
    config = Config()
except ValueError as e:
    # Print the error and exit gracefully if config fails to load.
    print(e)
    config = None