# ollama_api.py - используй встроенный API
import requests
import json

class OllamaAPI:
    def __init__(self, host="localhost", port=11434):
        self.base_url = f"http://{host}:{port}"
        
    def generate(self, prompt, model="qwen2.5:7b", temperature=0.7):
        """Генерация текста через API"""
        url = f"{self.base_url}/api/generate"
        
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2000
            }
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                return f"Ошибка API: {response.status_code}"
        except Exception as e:
            return f"Ошибка подключения: {e}"
    
    def chat(self, messages, model="qwen2.5:7b"):
        """Chat completion через API (более новый метод)"""
        url = f"{self.base_url}/api/chat"
        
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['message']['content']
            else:
                return f"Ошибка API: {response.status_code}"
        except Exception as e:
            return f"Ошибка подключения: {e}"

# Использование
if __name__ == "__main__":
    # Убедись, что Ollama сервер запущен:
    # ollama serve
    
    ollama = OllamaAPI()
    
    # Простой запрос
    print("🤖 Тест 1: Простой запрос")
    response = ollama.generate("Привет! Как дела?")
    print(f"Ответ: {response}")
    
    print("\n" + "="*50 + "\n")
    
    # Chat completion
    print("🤖 Тест 2: Chat completion")
    messages = [
        {"role": "system", "content": "Ты полезный ассистент."},
        {"role": "user", "content": "Привет!"},
        {"role": "assistant", "content": "Привет! Чем могу помочь?"},
        {"role": "user", "content": "Расскажи о Python"}
    ]
    
    response = ollama.chat(messages)
    print(f"Ответ: {response[:200]}...")