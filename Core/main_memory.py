import asyncio
import json

from Core.llm_toolkit import ChatManager
from Core.llm_toolkit import get_structured_content_with_playwright

async def run_application():
    """The main application loop."""

    # Initialize the ChatManager once. It handles everything internally.
    chat_manager = ChatManager(memory_file="memory.json")
    
    print("\n--- AI Product Extractor ---")
    print("Provide a URL to scrape, give feedback, or type 'exit' to quit.")

    while True:
        user_input = input("\n[User]: ")
        if user_input.lower() == 'exit':
            break

        message_to_send = ""
        if user_input.startswith(('http://', 'https://')):
            print("\n--- [Step 1/2] Starting Web Scraper ---")
            scraped_content = await get_structured_content_with_playwright(user_input)
            if not scraped_content:
                print("Scraping failed. Please try another URL.")
                continue
            message_to_send = scraped_content
        else:
            message_to_send = user_input
        
        # The core interaction is now incredibly clean.
        print("\n--- [Step 2/2] Thinking with Memory ---")
        model_response_text = await chat_manager.send_message(message_to_send)

        if model_response_text:
            print("\n[AI Response]:")
            try:
                # Try to pretty-print if the response is JSON
                parsed_json = json.loads(model_response_text)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                # Otherwise, print the plain text response
                print(model_response_text)
        else:
            print("\n[AI Response]: Sorry, I encountered an error.")

if __name__ == "__main__":
    asyncio.run(run_application())