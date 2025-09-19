import asyncio
from dotenv import load_dotenv

load_dotenv()

from Core.utils.config import config
from Core.utils.utils import *
from DatabaseHandler.DatabaseHandler import DatabaseHandler
from Core.llm_toolkit import ChatManager
from Core.services.duck_search import CrawlerDuckDuckGo
from Core.services.heinemann_search import scrape_product_data
from Core.llm_toolkit import get_structured_content_with_playwright


async def run_application():
    """The main application loop."""

    db_handler = DatabaseHandler(config.sql_conn_string)
    chat_manager = ChatManager(config.google_api_key, config.gemini_model, memory_file=None)
    duck_crawler = await CrawlerDuckDuckGo.create(headless=False)

    items = db_handler.get_items() 

    if not items:
        print(" --- All products have StatusDescription set to 1 ---\n\nClosing...")
        await duck_crawler.close()
        return
    
    for index, item in enumerate(items["products"]):
        try:
            links = await duck_crawler.search_product(item)

            heinemann_links = [link for link in links if ("heinemann-shop.com" in link and "/p/" in link)]
            if heinemann_links:
                #print("Found heinemann site, scraping directly...")
                #print(heinemann_links)
                response_dict = await scrape_product_data(heinemann_links[0])
                db_handler.add_or_update_description(items["product_id"][index],response_dict["product_name"], response_dict["description"],heinemann_links[0])
                db_handler.add_or_update_specifications(items["product_id"][index],response_dict["specifications"])
                continue

            for link in links:

                scraped_content = await get_structured_content_with_playwright(link)
                
                if scraped_content == "":
                    continue
                model_response_text, _ = await chat_manager.send_message(scraped_content)
            
                response_dict: dict = extract_json_from_string(model_response_text)

                if response_dict is None:
                    continue
                
                if information_completed(response_dict):
                    db_handler.add_or_update_description(items["product_id"][index],response_dict["product_name"], response_dict["description"],link)
                    db_handler.add_or_update_specifications(items["product_id"][index],response_dict["specifications"])
                    break
                else: print("Searching again...")

            

        except Exception as e:

            print(f"Failed to extract information for item {item},\n searched links {links}, \n model response {model_response_text}")
            print(e,end='\n\n')

    await duck_crawler.close()



if __name__ == "__main__":
    # If any keys were missing, the 'config' object would be None, and the program
    # would have already printed an error and exited the config.py file.
    if config is not None:
        asyncio.run(run_application())

