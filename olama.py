from typing import Optional
import requests
import json


class Client:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._check_connection()
    
    def _check_connection(self):
        """Проверяет подключение к Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                print("✅ Подключение к Ollama установлено")
            else:
                print("❌ Ollama не отвечает")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            print("Убедись что Ollama запущен: ollama serve")
    
    def list_models(self) -> list:
        """Список установленных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.json().get("models", [])
        except:
            return []
    
    def pull_model(self, model_name: str):
        """Скачивает модель"""
        print(f"📥 Скачиваю модель {model_name}...")
        response = requests.post(
            f"{self.base_url}/api/pull",
            json={"name": model_name},
            stream=True
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "status" in data:
                    print(f"Статус: {data['status']}")
    
    def generate(self, 
                prompt: str, 
                model: str = "llama2",
                max_tokens: int = 1000,
                temperature: float = 0.7) -> str:
        """Генерация текста"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            result = response.json()
            return result.get("response", "Ошибка генерации")
        except Exception as e:
            return f"Ошибка: {e}"

    def chat(self, messages: list, model: str = "llama2") -> str:
        """Чат-режим (более продвинутый)"""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120
        )
        return response.json()["message"]["content"]
main = Client()
print(main.generate("Привет как у тебя дела?"))    