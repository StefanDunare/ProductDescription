
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

def best_match(links):
    found_links = set()

    # --- Refined Parsing and Filtering Logic ---
    for link in links:
        
        # Simple check to avoid navigating to social media or video sites
        if any(domain in link for domain in ['pinterest.com', 'youtube.com', 'instagram.com', 'facebook.com', 'twitter.com']):
            continue

        # 1. Prioritize links from our known high-quality retailers
        if any(domain in link for domain in priority_domains):
            print(f"  [+] Found link from priority retailer: {link}")
            found_links.add(link)
            continue

        # 2. Check for URL patterns that strongly indicate a product page
        if any(pattern in link for pattern in product_page_patterns):
            print(f"  [+] Found likely product page (URL pattern match): {link}")
            found_links.add(link)
            continue

        # 3. Check for keywords in the page title
        # if any(keyword in title for keyword in product_title_keywords):
        #     print(f"  [+] Found likely product page (Title keyword match): {link}")
        #     found_links.add(link)
    
    if not found_links:
        return links
    return list(found_links)
    