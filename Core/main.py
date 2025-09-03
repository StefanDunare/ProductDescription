import asyncio

from Core.llm_toolkit import *


async def run_extraction_pipeline():

   # 1. Check for the essential API key before starting.
    if not GOOGLE_API_KEY:
        print("="*60)
        print("CRITICAL ERROR: The GOOGLE_API_KEY variable is not set.")
        print("Please set it before running the application (in this case, in llm_func.py).")
        print("="*60)
        return

    # 2. Get the target URL from the user.
    print("\n--- Product Information Extractor ---")
    product_url = input("Please enter the full product URL to scrape: ")
    if not product_url.startswith(('http://', 'https://')):
        print("Error: Invalid URL. Please provide a full URL starting with http:// or https://")
        return

    # 3. Define the data structure we want to get back from the LLM.
    # This schema can be easily customized for different needs.
    target_schema = {
        "product_name": "The full, official name of the product.",
        "description": "A detailed, multi-sentence summary of the product's features and purpose.",
        "specifications": "A dictionary (key-value pairs) of all available technical specifications."
    }

    # 4. Execute the pipeline steps by calling our imported functions.
    print("\n--- [Step 1/3] Starting Web Scraper ---")
    page_content = await get_structured_content_with_playwright(product_url)

    if not page_content:
        print("\n--- Pipeline Halted ---")
        print("Scraping failed. Cannot proceed to data extraction.")
        return

    print("\n--- [Step 2/3] Starting LLM Data Extraction ---")
    extracted_data = await extract_product_info_with_gemini(page_content, target_schema)

    # 5. Display the final results.
    print("\n--- [Step 3/3] Displaying Final Results ---")
    if extracted_data:
        print("\n" + "="*60)
        print("✅ EXTRACTION COMPLETE")
        print("="*60 + "\n")
        print(f"Product Name: {extracted_data.get('product_name', 'Not found')}\n")
        print(f"Description:\n{extracted_data.get('description', 'Not found')}\n")
        
        specifications = extracted_data.get('specifications', {})
        print("Specifications:")
        if isinstance(specifications, dict) and specifications:
            for key, value in specifications.items():
                print(f"  - {key}: {value}")
        elif isinstance(specifications, list) and specifications:
            for item in specifications:
                print(f"  - {item}")
        else:
            print("  No specifications found.")
        
        print("\n" + "="*60)
    else:
        print("\n" + "="*60)
        print("❌ EXTRACTION FAILED")
        print("="*60)
        print("The LLM was unable to extract data from the scraped content.")

if __name__ == "__main__":
    # This is the entry point of our application.
    asyncio.run(run_extraction_pipeline())
