import os
import json
import asyncio
import json
import google.generativeai as genai
from playwright.async_api import async_playwright, Page
from playwright_stealth.stealth import Stealth
from fake_useragent import UserAgent

# --- Configuration ---
GEMINI_MODEL = "gemini-2.5-flash-lite"
GOOGLE_API_KEY = "AIzaSyBADAnWugYt4uZzpm58_MDxcPxmZdh6Hqo"
MAX_HISTORY_TOKENS = 28000

class ChatManager:
    """
    Manages the state and interaction of a single, continuous conversation
    with an LLM, using a JSON file for persistence.
    """
    def __init__(self, api_key, gemini_model, memory_file: str):
        self.api_key = api_key
        self.gemini_model = gemini_model
        self.memory_file = memory_file
        self.system_prompt = ""
        self.history = []
        self.model = None
        self._initialize()

    def _initialize(self):
        """Loads memory from the file and initializes the generative model."""
        self._load_memory()
        
        # Initialize the model once
        print("Initializing Generative Model... ",end='')
        
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel(
            self.gemini_model,
            system_instruction=self.system_prompt
        )

    def _load_memory(self):
        """Loads memory from the file, or creates it if it doesn't exist."""

        self.system_prompt = create_structure_intial_prompt()
        if not self.memory_file:
             print("Running chat with no memory...", end='')
             return
        
        if not os.path.exists(self.memory_file):
            print(f"Creating '{self.memory_file}'.")
            self._save_memory()
        else:
            print(f"Loading memory from '{self.memory_file}'... ",end='')
            with open(self.memory_file, 'r') as f:
                memory_data = json.load(f)
                self.history = memory_data["history"]
            print("Done.")

    def _save_memory(self):
        """Saves the current state of the history to the JSON file."""
        with open(self.memory_file, 'w') as f:
            json.dump({"history": self.history}, f, indent=2)
    
    async def _prune_history_by_tokens(self):
        """
        Checks the history's token count and removes the oldest turns
        until it is within the defined limit.
        """
        while True:
            # Check the token count of the current history
            token_count = (await self.model.count_tokens_async(self.history)).total_tokens
            
            if token_count > MAX_HISTORY_TOKENS:
                print(f"History token count ({token_count}) exceeds max of {MAX_HISTORY_TOKENS}. Pruning...")
                # Remove the oldest turn (1 user message + 1 model response)
                if len(self.history) >= 2:
                    self.history = self.history[2:]
                else:
                    # Failsafe for a very short but large history
                    self.history = []
                    break # Exit loop if history is emptied
            else:
                # The history is within the token limit, we can stop.
                print(f"History token count is {token_count} (within limit).")
                break


    async def send_message(self, user_message: str) -> str:
        """Handles a single turn of the conversation seamlessly."""
        print("Sending message to Gemini... ")
        try:
            chat = self.model.start_chat(history=self.history)
            response = await chat.send_message_async(user_message)
            print (response)
            if self.memory_file:
                self.history.append({'role': 'user', 'parts': [user_message]})
                self.history.append({'role': 'model', 'parts': [response.text]})
                self._save_memory()
                print("Successfully received response and saved memory.")

            return response.text, response._done
        except Exception as e:
            print(f"\n--- An Error Occurred with the Gemini API ---\nError: {e}")
            return None


async def remove_popups_and_overlays(page: Page):
    """
    Finds and surgically removes common popups, overlays, and banners from the page's HTML.
    This is a direct manipulation approach for efficient text extraction.
    """
    # print("Scanning for and removing popups and overlays...")

    # A comprehensive list of selectors targeting common overlays.
    # This list can be expanded over time with patterns from new sites.
    overlay_selectors = [
        # The 'i' at the end of each selector makes the match case-insensitive.
        '[id*="onetrust" i]',
        '[id*="cookie" i]',
        '[id*="consent" i]',
        '[class*="cookie" i]',
        '[class*="consent" i]',
        '[class*="banner" i]',
        '.cc-banner',
        
        '[class*="modal" i]',
        '[class*="overlay" i]',
        '[role="dialog" i]',
        
        '[id*="newsletter" i]',
        '[class*="newsletter" i]',
    ]
    
    selectors_to_remove_str = ", ".join(overlay_selectors)
    
    try:
        # This script finds all elements matching any of our patterns and removes them.
        removed_count = await page.evaluate(f"""() => {{
            const elements = document.querySelectorAll('{selectors_to_remove_str}');
            let count = 0;
            elements.forEach(el => {{
                // The safety check remains, making the script resilient to weird pages (e.g., framesets)
                if (document.body && document.body.contains(el)) {{
                    el.remove();
                    count++;
                }}
            }});
            return count;
        }}""")
        
        if removed_count > 0:
            print(f"  [+] Success: Surgically removed {removed_count} overlay element(s).")
        else:
            print("  [-] No common popups or overlays were found to remove.")

    except Exception as e:
        print(f"  [!] An error occurred during popup removal: {e}")


async def get_structured_content_with_playwright(
    url: str,
    storage_state_path: str = None
) -> str:
    """
    Scrapes a URL using Playwright with a highly realistic browser persona.

    This function uses stealth, a realistic user agent, and consistent
    localization settings (locale, timezone, headers) to evade bot detection.
    It can also load a storage state to appear as a logged-in/returning user.

    Args:
        url: The URL to scrape.
        storage_state_path: Optional path to a storage state JSON file for authentication.

    Returns:
        A string with the structured page content, or an empty string on failure.
    """
    # print(f"Initializing advanced scraper for URL: {url}...")
    
    ua = UserAgent()
    user_agent = ua.chrome
    # print(f"Using User Agent: {user_agent}")
    
    # Let's create a consistent European persona
    persona_locale = 'en-GB'
    persona_timezone = 'Europe/London'

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=False,
            # channel="chrome",
            args=['--start-maximized']
        )
        
        # --- Building the Advanced Context ---
        context = await browser.new_context(
            # Basic Persona
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            
            # Localization Persona
            locale=persona_locale,
            timezone_id=persona_timezone,
            extra_http_headers={"Accept-Language": f"{persona_locale},en;q=0.9"},
            
            # Security & Performance
            ignore_https_errors=True, # Good practice for scrapers
            java_script_enabled=True, # Ensure JS is on
            
            # State Management for returning user / login
            storage_state=storage_state_path
        )
        
        page = await context.new_page()

        
        try:
            # print(f"Navigating with persona: Locale={persona_locale}, Timezone={persona_timezone}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            # print(f"Scraping {url}...")
            await remove_popups_and_overlays(page)
            await page.wait_for_timeout(1000)

            selector = 'h1, h2, h3, p, li, th, td, span, div'
            
            
            content_handle = await page.query_selector("body")
            try:
                await content_handle.evaluate("""(element) => {
                    const selectorsToRemove = ['script', 'style', 'nav', 'aside', 'form'];
                    selectorsToRemove.forEach(selector => {
                        element.querySelectorAll(selector).forEach(el => el.remove());
                    });
                }""")
            except AttributeError as e:
                print("Pagina fara body...")
                print(page.inner_html)
                return ""

            # elements_data = await page.eval_on_selector_all(selector, """(elements) =>
            #     elements.map(el => ({
            #         tag: el.tagName.toUpperCase(),
            #         text: el.textContent.trim()
            #     })).filter(el => el.text)
            # """)

            elements_data = await content_handle.eval_on_selector_all(selector, """(elements) =>
                elements.map(el => {
                    const isVisible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                    
                    // 1. Get the raw text content
                    let rawText = el.textContent;
                    
                    // 2. Perform NFKC normalization. This single command handles a huge
                    //    range of characters (typographic quotes, special spaces, ligatures, etc.)
                    //    in a standardized way without destroying important international characters.
                    let normalizedText = rawText.normalize('NFKC');
                    
                    // 3. Collapse any remaining messy whitespace into single spaces.
                    normalizedText = normalizedText.replace(/\\s+/g, ' ').trim();                                                  

                    return {
                        tag: el.tagName.toUpperCase(),
                        text: normalizedText, // Use the cleaned, normalized text
                        visible: isVisible
                    }
                })
                .filter(el => el.text && el.visible)
            """)

            structured_text_lines = [f"TAG:{item['tag']} | CONTENT: {item['text']}" for item in elements_data]
            
            print("Successfully scraped and structured page content.")
            return "\n".join(structured_text_lines)

        except Exception as e:
            print(f"\n--- An Error Occurred During Scraping ---\nError: {e}")
            return ""
        finally:
            # You might want to save the state after interacting
            # if not using a pre-saved one, e.g.:
            # await context.storage_state(path="latest_session.json")
            print("Closing browser...")
            await browser.close()


def create_structure_aware_prompt(structured_content: str, schema: dict) -> str:
    """
    Creates a robust, generalized prompt for an LLM to extract product information.

    This function builds a prompt that teaches the LLM how to analyze varied
    webpage structures by providing general strategies rather than rigid rules,
    making it more adaptable to different site layouts.

    Args:
        structured_content: The string from the scraper (e.g., "TAG:H1 | CONTENT: Title").
        schema: A dictionary defining the desired data (e.g., {"product_name": "..."}).

    Returns:
        A complete, formatted prompt string ready to be sent to the Gemini API.
    """
    
    # These are the general, flexible strategies we'll give the LLM.
    guidelines = {
        "product_name": "This is typically the most prominent headline at the top of the page. Prioritize text from `H1` tags, but also consider `H2`s or other large, standalone text near the beginning if the `H1` seems generic or incorrect.",
        "description": "Look for one or more consecutive paragraphs (`P` tags) that describe the product's main features and purpose. This should be descriptive text, not short marketing taglines, customer reviews, technical lists, or shipping information.",
        "specifications": "This information is often found in structured elements. Look for `TABLE`s (with `TH` and `TD` tags) or `UL`/`LI` lists. It can also appear as lines of text with a clear 'Key: Value' format (e.g., 'Color: Red'). Gather these attributes into a dictionary."
    }

    # We will dynamically build the schema details for the prompt.
    schema_details = []
    for key, description in schema.items():
        # Use our guideline for the key, with a fallback for custom keys.
        guideline = guidelines.get(key, "Extract this data as accurately as possible based on the content.")
        
        schema_details.append(
            f'\n- For the key "{key}":'
            f'\n  - Your Goal: {description}'
            f'\n  - General Strategy: {guideline}'
        )
    
    schema_string = "\n".join(schema_details)

    # Assemble the final prompt.
    prompt = f"""
You are an expert web content analyst specializing in product information extraction.
The content I provide is a simplified representation of a webpage's structure, with each line prefixed by its HTML tag (e.g., 'TAG:H1', 'TAG:P').

Your mission is to analyze this structured content and accurately extract the information based on the following schema and guidelines, formatting it into a single, clean JSON object.

---
**EXTRACTION SCHEMA AND GUIDELINES**
{schema_string}
---

**CRITICAL INSTRUCTIONS:**
1.  Analyze the provided content step-by-step using the strategies above.
2.  Your output MUST be a single, minified JSON object. Do not include any other text, explanations, or markdown formatting like ```json.
3.  If a piece of information cannot be found for any field, you MUST use the value "Not found". Do not invent data.

---
**STRUCTURED WEBSITE CONTENT**
{structured_content[:15000]}
---

**JSON_OUTPUT:**
"""
    return prompt

def create_structure_intial_prompt():
    # These are the general, flexible strategies we'll give the LLM.
    guidelines = {
        "product_name": "This is typically the most prominent headline at the top of the page. Prioritize text from `H1` tags, but also consider `H2`s or other large, standalone text near the beginning if the `H1` seems generic or incorrect.",
        "description": "Look for one or more consecutive paragraphs (`P` tags) that describe the product's main features and purpose. This should be descriptive text, not short marketing taglines, customer reviews, technical lists, or shipping information.",
        "specifications": "This information is often found in structured elements. Look for `TABLE`s (with `TH` and `TD` tags) or `UL`/`LI` lists. It can also appear as lines of text with a clear 'Key: Value' format (e.g., 'Color: Red'). Gather these attributes into a dictionary."
    }

    target_schema = {
        "product_name": "The full, official name of the product.",
        "description": "A detailed, multi-sentence summary of the product's features and purpose, translated into Romanian.",
        "specifications": "A dictionary (key-value pairs) of all available technical specifications, with both the attribute names (keys) and their values translated into Romanian."
    }

    # We will dynamically build the schema details for the prompt.
    schema_details = []
    for key, description in target_schema.items():
        # Use our guideline for the key, with a fallback for custom keys.
        guideline = guidelines.get(key, "Extract this data as accurately as possible based on the content.")
        
        schema_details.append(
            f'\n- For the key "{key}":'
            f'\n  - Your Goal: {description}'
            f'\n  - General Strategy: {guideline}'
        )
    
    schema_string = "\n".join(schema_details)

    # Assemble the final prompt.
    prompt = f"""
You are an romanian expert web content analyst specializing in product information extraction.
The content I provide is a simplified representation of a webpage's structure, with each line prefixed by its HTML tag (e.g., 'TAG:H1', 'TAG:P').

Your mission is to analyze this structured content and accurately extract and translate the information into romanian based on the following schema and guidelines, formatting it into a single, clean JSON object.
When I provide you with structured content, your task is to extract the information, **translate all relevant text into Romanian**, and then respond ONLY with a single, minified JSON object based on the following schema:

---
**EXTRACTION SCHEMA AND GUIDELINES**
{schema_string}
---

**CRITICAL INSTRUCTIONS:**
1.  Analyze the provided content step-by-step using the strategies above.
2.  Your output MUST be a single, minified JSON object. Do not include any other text, explanations, or markdown formatting like ```json.
3.  If a piece of information cannot be found for any field, you MUST use the value "Not found". Do not invent data, but you can translate.
4.  If you find any physical addresses in the content (e.g., street names, cities, postal codes, P.O. boxes), you MUST NOT include them in the final JSON output. Exclude them completely.

---
**From now you will either recieve STRUCTURED WEBSITE CONTENT or feedback that you must account for**

"""
    return prompt

def create_structure_intial_romanian_prompt():
    # These are the general, flexible strategies we'll give the LLM.
    guidelines = {
        "product_name": "Acesta este de obicei titlul cel mai proeminent din partea de sus a paginii. Acordă prioritate textului din etichetele `H1`, dar ia în considerare și etichetele `H2` sau alt text de mari dimensiuni, independent, de la începutul paginii, dacă `H1` pare generic sau incorect.",
        "description": "Caută unul sau mai multe paragrafe consecutive (`P` tags) care descriu caracteristicile principale ale produsului. Acesta ar trebui să fie un text descriptiv, nu sloganuri scurte de marketing, recenzii ale clienților, liste tehnice sau informații de livrare.",
        "specifications": "Această informație se găsește adesea în elemente structurate. Caută `TABLE`s (cu etichete `TH` și `TD`) sau liste `UL`/`LI`. Poate apărea și sub formă de linii de text cu un format clar 'Cheie: Valoare' (ex: 'Culoare: Roșu'). Adună aceste atribute într-un dicționar și tradu cheile si valorile."
    }

    target_schema = {
        "product_name": "Numele complet, oficial al produsului.",
        "description": "Un rezumat detaliat, în mai multe propoziții, al caracteristicilor și scopului produsului.",
        "specifications": "Un dicționar (perechi cheie-valoare) cu toate specificațiile tehnice disponibile."
    }

    # We will dynamically build the schema details for the prompt.
    schema_details = []
    for key, description in target_schema.items():
        # Use our guideline for the key, with a fallback for custom keys.
        guideline = guidelines.get(key, "Extract this data as accurately as possible based on the content.")
        
        schema_details.append(
            f'\n- Pentru cheia "{key}":'
            f'\n  - Obiectivul tău: {description}'
            f'\n  - Strategie Generală: {guideline}'
        )
    
    schema_string = "\n".join(schema_details)

    # Assemble the final prompt.
    prompt = f"""
Ești un analist expert al conținutului web, specializat în extragerea informațiilor despre produse.
Conținutul pe care îl furnizez este o reprezentare simplificată a structurii unei pagini web, fiecare linie fiind prefixată cu eticheta sa HTML (ex: 'TAG:H1', 'TAG:P').

Misiunea ta este să analizezi acest conținut structurat și să extragi și să traduci cu precizie informațiile, conform schemei și ghidului de mai jos, formatându-le într-un singur obiect JSON, curat.

---
**SCHEMA DE EXTRAGERE ȘI GHID**
{schema_string}
---

**INSTRUCȚIUNI CRITICE:**
1. Analizează conținutul furnizat pas cu pas folosind strategiile de mai sus.
2. Rezultatul tău TREBUIE să fie un singur obiect JSON, minified (compact). Nu include niciun alt text, explicații sau formatare markdown precum ```json.
3. Dacă o informație nu poate fi găsită pentru un câmp, TREBUIE să folosești valoarea "Not found".
4. Dacă găsești adrese fizice în conținut (ex: nume de străzi, orașe, coduri poștale, căsuțe poștale), NU TREBUIE să le incluzi în obiectul JSON final. Exclude-le complet.
---
**De acum înainte, vei primi CONȚINUT STRUCTURAT DE PE WEBSITE.**

"""
    return prompt


async def extract_product_info_with_gemini(
    structured_content: str, 
    schema: dict
) -> dict:
    """
    Sends scraped content to the Gemini API for information extraction.

    This function configures the API, generates a detailed prompt, sends the
    request, and then cleans and parses the JSON response.

    Args:
        structured_content: The structured string from the Playwright scraper.
        schema: A dictionary defining the desired data structure.

    Returns:
        A dictionary containing the extracted data, or None if an error occurs.
    """
    print("Initializing Gemini API connection...")

    if not structured_content:
        print("Error: Content to analyze is empty. Skipping API call.")
        return None
    
    try:
        # 1. Securely configure the API key
        api_key = GOOGLE_API_KEY
        if not api_key:
            raise ValueError("CRITICAL: GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)

        # 2. Call our other function to generate the prompt
        prompt = create_structure_aware_prompt(structured_content, schema)
        
        # 3. Initialize the model and make the async API call
        print("Sending request to Gemini model...")
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = await model.generate_content_async(prompt)
        
        # 4. Clean and parse the response
        # The model sometimes wraps the JSON in markdown, so we remove it.
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        
        print("Successfully received and cleaned response.")
        return json.loads(cleaned_response)

    except Exception as e:
        print(f"\n--- An Error Occurred with the Gemini API ---")
        print(f"Error: {e}")
        # Log the problematic response text if it exists, for debugging.
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Problematic raw response from API: {response.text}")
        return None

async def main():
    link = input("Test playwright get: ")
    with open("playwrighttest.txt", 'w') as f:
            #json.dump(await get_structured_content_with_playwright(link), f, indent=2)
            f.write(await get_structured_content_with_playwright(link))

if __name__ == "__main__":
    asyncio.run(main())