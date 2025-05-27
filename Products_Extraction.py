import asyncio
import random
import pandas as pd
from tqdm.asyncio import tqdm_asyncio
import tls_client

product_urls = pd.read_csv('scraped_urls.csv')['urls'].tolist()

API_URL = 'https://www.ashleyfurniture.com/on/demandware.store/Sites-Ashley-US-Site/default/Product-ProductDetailsJson'

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

product_specs = []
semaphore = asyncio.Semaphore(10)

# Create a single TLS session for reuse
tls_session = tls_client.Session(
    client_identifier="chrome_120",  # Simulates Chrome browser
    random_tls_extension_order=True
)

def sync_fetch_product_data(url):
    sku = url.split('/')[-1].split('.html')[0]
    params = {'sku': sku}
    headers = Headers_Temp.copy()
    headers['referer'] = url

    try:
        response = tls_session.get(API_URL, headers=headers, params=params, timeout=40)
        data = response.json()
        data['Product_URL'] = url
        return data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {'Product_URL': url, 'error': str(e)}

async def fetch_product_data(url):
    await asyncio.sleep(random.uniform(1, 5))
    async with semaphore:
        return await asyncio.to_thread(sync_fetch_product_data, url)

async def main():
    tasks = [fetch_product_data(url) for url in product_urls]
    for coro in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Scraping"):
        result = await coro
        product_specs.append(result)

asyncio.run(main())

df = pd.DataFrame(product_specs)
df.to_csv("scraped_products.csv", index=False)
