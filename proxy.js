// Cloudflare Worker Proxy для безопасной отправки данных
export default {
  async fetch(request) {
    // Только POST запросы
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }
    
    try {
      // Получаем данные из запроса
      const requestData = await request.json();
      
      // Отправляем на ваш локальный API
      const response = await fetch('http://51.38.54.50:8000/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      
      // Возвращаем ответ от вашего API
      return new Response(response.body, {
        status: response.status,
        headers: response.headers
      });
      
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};
