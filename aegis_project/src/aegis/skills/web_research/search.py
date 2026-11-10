import httpx
import trafilatura
from typing import Any, List, Dict

class WebSearcher:
    """
    Асинхронный поисковый двигатель и текстовый скрапер интернета.
    Выходит в сеть через DuckDuckGo API и очищает HTML до чистого Markdown через trafilatura.
    """
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout = timeout_seconds
        # Настраиваем заголовки User-Agent, чтобы сайты не блокировали нашего робота
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search_links(self, query: str, max_results: int = 3) -> List[str]:
        """
        Выполняет поиск в DuckDuckGo через быстрое легковесное API.
        Возвращает список из найденных URL-ссылок.
        """
        url = f"https://duckduckgo.com{query}"
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            
            # Быстрый сбор ссылок из HTML-разметки DuckDuckGo
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            links = []
            
            for a in soup.find_all("a", class_="result__url"):
                href = a.get("href")
                if href and href.startswith("http"):
                    links.append(href)
                    if len(links) >= max_results:
                        break
            return links

    async def scrape_page(self, url: str) -> Dict[str, Any]:
        """
        Асинхронно скачивает веб-страницу и рафинирует её до чистого Markdown текста.
        """
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return {"url": url, "text": "", "error": f"HTTP {response.status_code}"}
                
                # Главное действие: trafilatura вычищает разметку, рекламу и меню, оставляя только суть
                downloaded = response.text
                cleaned_text = trafilatura.extract(downloaded, include_links=False, include_images=False)
                
                return {
                    "url": url,
                    "text": cleaned_text if cleaned_text else "",
                    "error": None
                }
        except Exception as e:
            return {"url": url, "text": "", "error": str(e)}
