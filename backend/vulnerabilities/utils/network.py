import asyncio
import aiohttp


async def fetch_single_patch(session, url, semaphore):
    """
    Fetches the raw git patch text from a GitHub commit URL.
    """
    patch_url = f"{url}.patch" if "commit" in url and not url.endswith(".patch") else url
    async with semaphore:
        try:
            async with session.get(patch_url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            print(f"Error fetching patch from {patch_url}: {e}")
            return None


async def fetch_all_github_patches(github_urls, github_token):
    """
    Fetches multiple GitHub patches while respecting rate limits.
    """
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.patch"
    } if github_token else {}

    # Limit concurrency to avoid hitting GitHub API rate limits too hard
    semaphore = asyncio.Semaphore(10)
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_single_patch(session, url, semaphore) for url in github_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [res for res in results if isinstance(res, str)]


async def fetch_osv_data(ecosystem, package_name):
    """
    Queries the OSV database for known vulnerabilities in a specific package.
    """
    url = "https://api.osv.dev/v1/query"
    payload = {"package": {"name": package_name, "ecosystem": ecosystem}}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            return {"vulns": []}
