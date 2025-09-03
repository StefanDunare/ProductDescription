import asyncio
from dotenv import load_dotenv
import json
# Load the .env file BEFORE you import your config and other modules.
# This ensures the variables are available when the classes are defined.
load_dotenv()

# Now, import your components. The config will be automatically validated here.
from Core.utils.config import config
from Core.utils.utils import *
from DatabaseHandler.DatabaseHandler import DatabaseHandler
from Core.llm_toolkit import ChatManager
from Core.services.google_search import search_for_product_links
from Core.services.duck_search import CrawlerDuckDuckGo
from Core.llm_toolkit import get_structured_content_with_playwright


async def run_application():
    """The main application loop."""

    # --- THE CHECK IS NOW AUTOMATIC ---
    # If any keys were missing, the 'config' object would be None, and the program
    # would have already printed an error and exited the config.py file.
    if config is None:
        return # Exit gracefully

    db_handler = DatabaseHandler(config.sql_conn_string)

    chat_manager = ChatManager(config.google_api_key, config.gemini_model, memory_file=None)

    items = db_handler.get_items() # querry for the items with StatusDescription 0


    scraped_content = await get_structured_content_with_playwright("https://www.douglas.ro/p/givenchy-pi-eau-de-toilette-340024?trac=DO_RO.01.01_Shopping.P_Shopping.Google.15415210270.159067054310.340024.online.PM&gad_source=1&gad_campaignid=15415210270&gbraid=0AAAAADixG-xHuzjf5KWCWC6talTSJAkR6&gclid=Cj0KCQjwqqDFBhDhARIsAIHTlkuUJ43RbQDw55BmAji_wwt_FNxvPiG9Me3-pXgT0cJCZHzgy3PJh6waAnoUEALw_wcB")
    
    model_response_text = await chat_manager.send_message(scraped_content)
    
    response_dict: dict = json.loads(model_response_text)

    db_handler.add_or_update_description("id1",response_dict["product_name"], response_dict["description"])

    db_handler.add_or_update_specifications("id1",response_dict["specifications"])





















    duck_crawler = await CrawlerDuckDuckGo.create(headless=False)

    




    # for item in items["products"][:5]:
    #     # links, all_links = search_for_product_links(item)
    #     links = duck_crawler.search_product(item)

    #     best_links = best_match(links)


    #     if linkuri:
    #         print("\nURL-uri găsite:")
    #         for idx, link in enumerate(linkuri):
    #             print(f"{idx+1}: {link}")

    # product_id = "P123456"
    # product_name = "aasdasd"
    # product_description = "asdasegeg"
    # db_handler.add_or_update_description(product_id, product_name, product_description)


    # The rest of your application can now safely assume all configs are present.
    # chat_manager = ChatManager(
    #     memory_file="memory.json",
    #     system_prompt=get_system_prompt()
    # )
    
    # ... (the rest of your application loop is the same)

    await duck_crawler.close()
    
if __name__ == "__main__":
    asyncio.run(run_application())

