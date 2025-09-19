# Product Description Generator

This project is an automated system designed to find and generate product descriptions and specifications using web scraping and a Generative AI model (Google Gemini). It reads products from a database that are missing a description, searches for them online, scrapes the relevant product pages, and uses an AI to intelligently extract and structure the information.

## How It Works

The workflow is as follows:
1.  **Database Input**: The script identifies products in the `Desc_Product` table that have a `Status Description` of `0`, marking them as needing a description.
2.  **Web Search**: For each product, the system automatically searches online to find the most relevant product page URL.
3.  **Intelligent Scraping**: Using Playwright, the script navigates to the found URL, handles popups and anti-bot measures, and extracts the clean, relevant text content from the page.
4.  **AI Data Extraction**: The cleaned content is sent to the Gemini Large Language Model, which analyzes the text and extracts structured data (product name, description, specifications) based on a sophisticated system prompt.
5.  **Database Update**: The structured data is then used to update the product's entry in the database.


## 🚀 Getting Started

### 1. Prerequisites

-   Python 3.9+
-   Microsoft SQL Server database access.

### 2. Setup

**Step 1: Database & Environment**
-   Add products to the `Desc_Product` table in your database. You can use `Insert into table_updated.sql` as a template.
-   Create a `.env` file in the project root and add your configuration variables:
    ```env
    # Gemini API
    GEMINI_MODEL="gemini-1.5-flash"
    GOOGLE_API_KEY="your_google_api_key_here"

    # SQL Server ODBC Connection String
    SQL_CONN_STRING="UID=your_username;PWD=your_password"
    ```
**Note:** The `SQL_CONN_STRING` only contains the username and password.

**Step 2: Install Dependencies**
-   It is recommended to use a virtual environment.
-   Install all required Python packages and the necessary browser binaries with these two commands:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

### 3. Running the Script

The application will automatically find and process all products in the database that have a `Status Description` of `0`.
