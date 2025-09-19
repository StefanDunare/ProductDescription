import re
import json
import google.generativeai as genai
from playwright.async_api import async_playwright, Page, Locator, TimeoutError, expect

from Core.utils.config import config
from Core.utils.utils import extract_json_from_string


product_data = {}
curent_index = ""

"""helper functions"""
def clean_string(text):
    """A helper function to clean up whitespace and special characters."""
    # Replace the non-breaking space (\u00a0) with a regular space
    # and strip any leading/trailing whitespace.
    return text.replace('\u00a0', ' ').strip()
def parse_table_data(messy_dict):
    """
    Takes a dictionary with messy, multi-line keys and values,
    and returns a clean, structured dictionary.
    """
    clean_dict = {}
    
    # Iterate through each key-value pair in your scraped data
    for messy_key, messy_value in messy_dict.items():
        # Split the key and value strings into lists based on the newline character
        keys = messy_key.split('\n')
        values = messy_value.split('\n')
        
        # Check for a consistent number of sub-keys and sub-values
        if len(keys) != len(values):
            # If they don't match, it's safer to just clean the original entry
            clean_dict[clean_string(messy_key.replace('\n', ' '))] = clean_string(messy_value.replace('\n', ' '))
            continue

        # The first key is the main category (e.g., "Fat")
        main_key = clean_string(keys[0])
        
        # The first value corresponds to the main key
        clean_dict[main_key] = clean_string(values[0])
        
        # Process the rest of the sub-keys (if any)
        # We start from the second item (index 1)
        if len(keys) > 1:
            for i in range(1, len(keys)):
                # Create a new, descriptive key, e.g., "Fat - of which saturates fat"
                sub_key_part = clean_string(keys[i])
                
                # A simple way to handle "of which" is to check if it's already there
                if "of which" in sub_key_part.lower():
                     # Remove "of which" if it's there to avoid "Fat - of which of which..."
                    sub_key_part = re.sub(r'of which', '', sub_key_part, flags=re.IGNORECASE).strip()

                new_key = f"{main_key} - of which {sub_key_part}"
                
                # Assign the corresponding value
                clean_dict[new_key] = clean_string(values[i])

    return clean_dict

async def get_table(locator: Locator):
    result = {}
    count = await locator.count()
    if count > 0:
        rows = await locator.all()
        rows = await rows[0].locator("tr").all()

        for row in rows:
            cells = await row.locator("td").all()
            if len(cells) == 2:
                key = (await cells[0].inner_text()).strip()
                value = (await cells[1].inner_text()).strip()
                if key and value: # Ensure we don't add empty entries
                   result[key] = value
    return parse_table_data(result)  


async def determine_next_step(element: Locator):
    global curent_index
    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
    match tag_name:
        case "h2":
            curent_index = await element.inner_text()
            return 
        case "div":
            div_dict = {}
            i = 0
            elements = await get_div_children(element)
            for elem in elements:
                data = await determine_next_step(elem)
                if data is not None and data != "":
                    div_dict[i] = data
                    i = i + 1
            return div_dict
        case "p":
            return(await element.inner_text())
        case "table":
            return await get_table(element) 
        case default:
            raise RuntimeWarning(f"Untreated tag in determine_next_step(): {tag_name}")



async def get_div_children(container: Locator) -> list[str]:
    
    if container.count == 0:
        return []
    child_elements = await container.locator("> *").all()
    if len(child_elements) == 0:
        return []
    
    for i, element in enumerate(child_elements):
        # Here is the check:
        tag_name = await element.evaluate('el => el.tagName.toLowerCase()')

    return child_elements

async def scrape_product_data(url: str):
    """
    Navigates to a Heinemann product page and scrapes key information.

    Args:
        url: The URL of the product page.

    Returns:
        A dictionary containing the scraped product data, or None on failure.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            # Mimic a real browser to avoid being blocked
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Go to the page, wait until network is idle
            await page.goto(url, timeout=90000, wait_until='commit')
            
            try:
                await page.click("button:has-text('Accept all')")
            except:
                pass  # No cookie popup
            
            container_selector = "#product-page-content > div.mdc-layout-grid__cell--span-4-mobile-s.mdc-layout-grid__cell--span-6-mobile-l.mdc-layout-grid__cell--span-4-tablet.mdc-layout-grid__cell--span-5-desktop.mdc-layout-grid__cell--span-5-desktop-l > div.c-accordion.js-accordion.u-margin-top-xl"
            container = page.locator(container_selector).first
            elements: list[Locator] = []
            elements = await get_div_children(container)
            
            # --- 1. Scrape Product Name ---
            # E-commerce names are often in the main <h1> tag
            name_selector = "#product-page-content > div.mdc-layout-grid__cell--span-4-mobile-s.mdc-layout-grid__cell--span-6-mobile-l.mdc-layout-grid__cell--span-4-tablet.mdc-layout-grid__cell--span-5-desktop.mdc-layout-grid__cell--span-5-desktop-l > section > div > h1"
            product_data['Name'] = await page.locator(name_selector).inner_text()

            # --- 2. Scrape Price ---
            # Prices are often in a div or span with a class related to 'price'
            price_selector = "#product-order-card > div.c-order-card__price > div > div > p.c-price"
            product_data['Price'] = await page.locator(price_selector).inner_text()

            for i, elem in enumerate(elements):
                product_data[curent_index] = await determine_next_step(elem)
                

        except TimeoutError:
            print(f"Timeout Error: The page at {url} took too long to load.")
            return None
        except Exception as e:
            print(f"An error occurred while scraping {url}: {e}")
            return None
        finally:
            await browser.close()
        
        # Clean up the text data
        for key, value in product_data.items():
            if isinstance(value, str):
                product_data[key] = value.strip()

        return process_scraped_data(product_data)
    
# --- Functie generica pentru procesarea datelor scraped ---
def process_scraped_data(scraped_data: dict):
    # 1. Nume
    product_name = scraped_data.get('Name', '')

    # 2. Descriere: concatenăm toate textele din 'Product description'
    def extract_description(desc_dict):
        desc_list = []
        for v in desc_dict.values():
            if isinstance(v, dict):
                desc_list.extend([f"{k}: {val}" for k, val in v.items()])
            else:
                desc_list.append(v)
        return "\n".join(desc_list)
    
    product_description = extract_description(scraped_data.get('Product description', {}))

    # 3. Specificatii: combinam 'Product details', 'Ingredients', 'Taste' (daca exista)
    def extract_specs(data_dict):
        specs = {}
        for main_key in ['Product details', 'Ingredients', 'Taste']:
            sub_dict = data_dict.get(main_key, {})
            for v in sub_dict.values():
                if isinstance(v, dict):
                    specs.update(v)
                else:
                    if main_key in specs:
                        specs[main_key] += " " + v
                    else:
                        specs[main_key] = v
        return specs

    product_specs = extract_specs(scraped_data)

    result = {
        'product_name': product_name,
        'description': product_description,
        'specifications': product_specs
    }

    genai.configure(api_key=config.google_api_key)
    model = genai.GenerativeModel(config.gemini_model)
    response = model.generate_content(f"""
        You are an automated JSON translation service. Your task is to translate the **values** of a given JSON object from English to Romanian. You must follow these rules strictly:
        1.  Translate **only the string values**. Do not translate keys, numbers, booleans, or nulls.
        2.  The structure of the output JSON must be **identical** to the input JSON.
        3.  Do not add any explanations, comments, or markdown formatting. Respond ONLY with the translated JSON object.

        {json.dumps(result)}""")

    return extract_json_from_string(response.text)
