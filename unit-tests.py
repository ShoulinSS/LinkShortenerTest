import pytest
import string
from unittest.mock import Mock, patch
from pydantic import HttpUrl
from main import generate_id, shorten_link, redirect_link, get_stats, Link, UrlRequest

@pytest.fixture
def mock_db_session():
    db = Mock()
    
    mock_query = Mock()
    mock_filter = Mock()
    db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    
    mock_filter.first.return_value = None
    
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    
    return db

def test_generate_id():
    """Проверка корректности генерации сокращенной ссылки"""

    for length in [1, 6, 10, 20]:
        result = generate_id(length=length)
        assert len(result) == length
        assert isinstance(result, str)
        assert all(c in string.ascii_letters + string.digits for c in result)

@patch("main.generate_id")
def test_shorten_link(mock_generate, mock_db_session):
    """Проверка функции shorten_link, в частности корректности записываемых в БД данных"""

    mock_generate.return_value = "ABC123"
    
    request = UrlRequest(url=HttpUrl("https://example.com/"))
    
    result = shorten_link(request=request, db=mock_db_session)
    
    assert result == {"short_id": "ABC123"}
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    
    added_link = mock_db_session.add.call_args[0][0]
    assert isinstance(added_link, Link)
    assert added_link.short_id == "ABC123"
    assert added_link.original_url == "https://example.com/"
    assert added_link.usage_count in (None, 0)

@patch("main.RedirectResponse")
def test_redirect_link(mock_redirect, mock_db_session):
    """Проверка перенаправления на оригинальную ссылку, изменения счетчика в БД"""

    mock_link = Mock(spec=Link)
    mock_link.original_url = "https://example.com/"
    mock_link.usage_count = 0
    
    mock_db_session.query().filter().first.return_value = mock_link
    
    result = redirect_link(short_id="ABC123", db=mock_db_session)
    
    assert mock_link.usage_count == 1
    mock_db_session.commit.assert_called_once()
    mock_redirect.assert_called_once_with(url="https://example.com/", status_code=302)

def test_get_stats(mock_db_session):
    """Проверка получения статистики прохождения по сокращенной ссылке"""

    mock_link = Mock(spec=Link)
    mock_link.short_id = "ABC123"
    mock_link.usage_count = 2319
    
    mock_db_session.query().filter().first.return_value = mock_link
    
    result = get_stats(short_id="ABC123", db=mock_db_session)
    
    assert result == {"short_id": "ABC123", "usage_count": 2319}