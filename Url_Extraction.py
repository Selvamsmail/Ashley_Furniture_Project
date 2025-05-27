import asyncio
import random
import pandas as pd
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio
import tls_client

Headers_Temp = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
}

BASE_URL = 'https://www.ashleyfurniture.com/c/outdoor/outdoor-seating/'
AJAX_URL = BASE_URL
product_urls = []
semaphore = asyncio.Semaphore(10)

# Setup TLS client session (reused across threads)
tls_session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

def sync_fetch_html(start):
    params = {
        'start': start,
        'sz': '30',
        'format': 'ajax',
    }
    headers = Headers_Temp.copy()
    headers['referer'] = BASE_URL

    try:
        response = tls_session.get(AJAX_URL, headers=headers, params=params, timeout=20)
        return response.text
    except Exception as e:
        print(f"[ERROR] start={start}: {e}")
        return ""

async def fetch_html(start):
    await asyncio.sleep(random.uniform(1, 2))
    async with semaphore:
        return await asyncio.to_thread(sync_fetch_html, start)

async def get_total_pages():
    html = await fetch_html(30)
    soup = BeautifulSoup(html, 'html.parser')

    try:
        total_text = soup.select_one('.filter-sort-bar h2').text
        total_count = int(total_text.split('\n')[-4].strip())
        pages = total_count // 30 + (1 if total_count % 30 != 0 else 0)
        return pages
    except Exception as e:
        print(f"[ERROR] Could not determine number of pages: {e}")
        return 1

async def scrape_all_urls():
    total_pages = await get_total_pages()
    print(f"[INFO] Total pages found: {total_pages}")

    tasks = [fetch_html(i * 30) for i in range(total_pages)]
    for coro in tqdm_asyncio.as_completed(tasks, total=total_pages, desc="Scraping Pages"):
        html = await coro
        soup = BeautifulSoup(html, 'html.parser')
        urls = [a.get('href') for a in soup.select('.grid-tile .product-name a')]
        product_urls.extend(urls)
    print(f"[INFO] Scraped {len(product_urls)} product URLs.")

asyncio.run(scrape_all_urls())

# Save results
pd.DataFrame(product_urls, columns=['urls']).to_csv('scraped_urls.csv', index=False)
