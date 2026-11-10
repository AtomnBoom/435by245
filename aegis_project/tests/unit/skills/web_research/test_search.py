import pytest
# Исправлено: теперь импорт ведет строго в файл search.py по плану!
from src.aegis.skills.web_research.search import WebSearcher

@pytest.mark.asyncio
async def test_web_searcher_scrape_structure():
    """Тест: проверяем способность скрапера скачивать и вычищать текстовые страницы."""
    searcher = WebSearcher(timeout_seconds=5.0)
    
    # Используем стабильную текстовую страницу стандартов в сети
    test_url = "https://w3.org"
    
    result = await searcher.scrape_page(test_url)
    
    # Проверяем структуру возвращаемого ответа
    assert "url" in result
    assert "text" in result
    assert "error" in result
    
    # Если интернет на компьютере активен и страница скачалась — проверяем очистку от HTML-мусора
    if not result["error"]:
        assert len(result["text"]) > 0
        assert "<html" not in result["text"]
        assert "<body>" not in result["text"]
