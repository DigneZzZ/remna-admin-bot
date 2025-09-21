import httpx
import logging
import json
import asyncio
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

def get_headers():
    """Get headers for API requests"""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "RemnaBot/1.0",
        "Connection": "close"
    }

def get_client_kwargs():
    """Get httpx client configuration"""
    return {
        "timeout": 30.0,  # Reduced timeout for faster failure detection
        "verify": True,  # Enable SSL verification for HTTPS
        "headers": get_headers(),
        # More conservative connection limits to prevent exhaustion
        "limits": httpx.Limits(
            max_keepalive_connections=2, 
            max_connections=5, 
            keepalive_expiry=10  # Shorter keepalive to prevent stale connections
        ),
        # Force HTTP/1.1 for better compatibility
        "http2": False,
        # SSL configuration for HTTPS
        "cert": None,  # No client certificate
        "trust_env": False  # Don't use environment variables for proxy settings
    }

class RemnaAPI:
    """API client for Remnawave API using httpx"""
    
    @staticmethod
    async def _test_connection():
        """Test basic connectivity to the API server"""
        try:
            # Используем известный рабочий эндпоинт для проверки подключения
            url = f"{API_BASE_URL.rstrip('/')}/users"
            client_kwargs = get_client_kwargs()
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(url, timeout=10.0, follow_redirects=True)
                logger.debug(f"Тест подключения: статус {response.status_code}, URL: {response.url}")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Тест подключения не прошел: {e}")
            return False
    
    @staticmethod
    async def _make_request(method, endpoint, data=None, params=None, retry_count=3):
        """Make HTTP request with retry logic and proper error handling"""
        url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        
        logger.info(f"Making {method} request to: {url}")
        logger.debug(f"Request params: {params}")
        logger.debug(f"Request data: {data}")
        
        for attempt in range(retry_count):
            try:
                # Test connection on first attempt or after failures
                if attempt == 0 or attempt > 0:
                    if not await RemnaAPI._test_connection():
                        logger.warning(f"Тест подключения не прошел на попытке {attempt + 1}")
                        if attempt < retry_count - 1:
                            wait_time = 2 ** attempt
                            logger.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("Тест подключения не прошел на финальной попытке")
                            return None
                
                client_kwargs = get_client_kwargs()
                logger.debug(f"Client config: {client_kwargs}")
                
                async with httpx.AsyncClient(**client_kwargs) as client:
                    request_kwargs = {
                        'url': url,
                        'params': params
                    }
                    
                    if method.upper() in ['POST', 'PATCH', 'PUT'] and data is not None:
                        request_kwargs['json'] = data
                    
                    response = await client.request(method, follow_redirects=True, **request_kwargs)
                    
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    # Проверка статуса ответа
                    if response.status_code >= 500:
                        logger.warning(f"Ошибка сервера {response.status_code}, повторная попытка...")
                        if attempt < retry_count - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                    
                    response.raise_for_status()
                    
                    # Проверка Content-Type
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type.lower():
                        logger.error(f"Ожидался JSON, получен {content_type}. Ответ: {response.text[:500]}")
                        return None
                    
                    # Парсинг JSON
                    if not response.text.strip():
                        logger.warning("Получен пустой ответ")
                        return None
                    
                    json_response = response.json()
                    
                    # Обработка структуры ответа Remnawave API
                    if isinstance(json_response, dict):
                        if 'response' in json_response:
                            return json_response['response']
                        elif 'error' in json_response:
                            logger.error(f"API вернул ошибку: {json_response['error']}")
                            return None
                        else:
                            return json_response
                    
                    return json_response
                        
            except httpx.ConnectError as e:
                logger.error(f"Ошибка подключения на попытке {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Не удалось подключиться после {retry_count} попыток")
                    return None
                    
            except httpx.TimeoutException as e:
                logger.error(f"Превышено время ожидания на попытке {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"Повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Превышено время ожидания после {retry_count} попыток")
                    return None
                    
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 404:
                    logger.info(f"HTTP 404 для {url}: {e.response.text}")
                    return None
                logger.error(f"HTTP ошибка {status}: {e.response.text}")
                if status >= 500 and attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Ошибка сервера, повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    return None
                    
            except httpx.RemoteProtocolError as e:
                logger.error(f"Ошибка протокола на попытке {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Ошибка протокола, повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Ошибка протокола после {retry_count} попыток")
                    return None
                    
            except httpx.ConnectTimeout as e:
                logger.error(f"Таймаут подключения на попытке {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Таймаут подключения, повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Таймаут подключения после {retry_count} попыток")
                    return None
                    
            except httpx.ReadTimeout as e:
                logger.error(f"Таймаут чтения на попытке {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Таймаут чтения, повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Таймаут чтения после {retry_count} попыток")
                    return None
                    
            except Exception as e:
                logger.error(f"Неожиданная ошибка на попытке {attempt + 1}: {str(e)}")
                logger.debug(f"Тип исключения: {type(e).__name__}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Неожиданная ошибка, повторная попытка через {wait_time} секунд...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Неожиданная ошибка после {retry_count} попыток")
                    return None
        
        return None
    
    @staticmethod
    async def get(endpoint, params=None):
        """Make a GET request to the API"""
        return await RemnaAPI._make_request('GET', endpoint, params=params)
    
    @staticmethod
    async def post(endpoint, data=None):
        """Make a POST request to the API"""
        return await RemnaAPI._make_request('POST', endpoint, data=data)
    
    @staticmethod
    async def patch(endpoint, data=None):
        """Make a PATCH request to the API"""
        return await RemnaAPI._make_request('PATCH', endpoint, data=data)
    
    @staticmethod
    async def delete(endpoint, params=None):
        """Make a DELETE request to the API"""
        return await RemnaAPI._make_request('DELETE', endpoint, params=params)
    
    @staticmethod
    async def health_check():
        """Check API server health"""
        return await RemnaAPI._test_connection()
