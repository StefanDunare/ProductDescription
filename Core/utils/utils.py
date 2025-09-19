import json
import re

# Keywords often found in the URLs of product pages for your categories
product_page_patterns = [
    '/product/', '/products/', '/p/', '/dp/', '/item/', '/shop/',
    '/collection/', '/fragrances/', '/makeup/', '/skincare/', '/jewelry/'
]

# Keywords often found in the titles of retailer/product pages
product_title_keywords = [
    'buy', 'shop', 'price', 'add to cart', 'official site', 'view', 'eau de parfum'
]

# Domains to prioritize (major retailers and brands)
# This helps push relevant e-commerce sites to the top.
priority_domains = [
    'sephora.com', 'ulta.com', 'macys.com', 'nordstrom.com',
    'saksfifthavenue.com', 'bloomingdales.com', 'dillards.com',
    'amazon.com', 'walmart.com', 'target.com'
]

def best_match(links:list):
    found_links = []

    # --- Refined Parsing and Filtering Logic ---
    for link in links:

        # regex search heinemann product
        pattern = r'heinemann-shop.com.*/p/'
        if re.search(pattern, link):
            found_links.append(link)
            continue

        # Simple check to avoid navigating to social media or video sites
        if any(domain in link for domain in ['pinterest.com', 'youtube.com', 'instagram.com', 'facebook.com', 'twitter.com', '.fr','1001spirits.com']):
            links.remove(link)
            print(f"  [-] Removed link: {link}")
            continue
            
        # 1. Prioritize links from our known high-quality retailers
        if any(domain in link for domain in priority_domains):
            print(f"  [+] Found link from priority retailer: {link}")
            found_links.append(link)
            continue

        # 2. Check for URL patterns that strongly indicate a product page
        if any(pattern in link for pattern in product_page_patterns):
            print(f"  [+] Found likely product page (URL pattern match): {link}")
            found_links.append(link)
            continue

        # 3. Check for keywords in the page title
        # if any(keyword in title for keyword in product_title_keywords):
        #     print(f"  [+] Found likely product page (Title keyword match): {link}")
        #     found_links.add(link)
    
    if not found_links:
        return links
    return found_links
    

def extract_json_from_string(text: str) -> dict | None:
    
    if not text:
        return None

    try:
        # Find the starting position of the JSON object
        start_index = text.find('{')
        
        # Find the ending position of the JSON object (search from the right)
        end_index = text.rfind('}')
        
        # Check if both braces were found and in the correct order
        if start_index != -1 and end_index != -1 and end_index > start_index:
            # Slice the string to get the potential JSON part
            json_substring = text[start_index : end_index + 1]
            
            # Try to parse the extracted substring
            return json.loads(json_substring)
        else:
            # Braces were not found or were in the wrong order
            print("Error: Could not find a valid JSON object within the string.")
            return None
        
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse the extracted JSON substring. Reason: {e}")
        # Optionally, log the substring that failed:
        print(f"Substring that failed: {json_substring}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}")
        return None

def information_completed(items:dict):

    for value in items.values():
        if value == "Not found":
            return False
    return True
