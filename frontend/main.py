import streamlit as st
import numpy
import requests
import hashlib
import hmac
import time
import json
import uuid
from typing import Optional, List
from datetime import datetime

API_URL = "http://0.0.0.0:8080"
json_path_secrets = "/Users/ivan/AI-API/data/secrets.json"

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_siganture() -> str:
    try:
        with open(json_path_secrets, "r") as file:
            data = json.load(file)
        return data["signature"]
    except KeyError:
        raise KeyError("Key not Found")

def get_api_key() -> str:
    try:
        with open(json_path_secrets, "r") as file:
            data = json.load(file)
        return data["api"]    
    except KeyError:
        raise KeyError("Key not found")    

def generate_siganture(data: dict) -> str:
    KEY = get_siganture()
    data_to_ver = data.copy()
    data_to_ver.pop("signature", None)
    data_str = json.dumps(data_to_ver, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
    return str(expected_signature)

def hash_password(psw: str) -> str:
    byt = psw.encode("utf-8")
    return str(hashlib.sha256(byt).hexdigest())

# ========== API ФУНКЦИИ ==========

def register_api(username: str, psw: str) -> bool:
    data = {
        "username": username,
        "hash_psw": hash_password(psw)
    }
    headers = {
        "X-Signature": generate_siganture(data),
        "X-Timestamp": str(int(time.time()))
    }
    try:
        res = requests.post(f"{API_URL}/register", json=data, headers=headers)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Ошибка подключения к API: {e}")
        return False

def login(username: str, psw: str) -> bool:
    data = {
        "username": username,
        "hash_psw": psw
    }
    headers = {
        "X-Signature": generate_siganture(data),
        "X-Timestamp": str(int(time.time()))
    }
    try:
        res = requests.post(f"{API_URL}/login", json=data, headers=headers)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Ошибка подключения к API: {e}")
        return False

def create_new_chat(username: str) -> bool:
    data = {
        "username": username
    }
    headers = {
        "X-Signature": generate_siganture(data),
        "X-Timestamp": str(int(time.time()))
    }
    try:
        resp = requests.post(f"{API_URL}/create/new/chat", json=data, headers=headers)
        return resp.status_code == 200
    except Exception as e:
        st.error(f"Ошибка создания чата: {e}")
        return False

def get_user_chats(username: str):
    headers = {
        "X-API-KEY": get_api_key()
    }
    try:
        res = requests.get(f"{API_URL}/get/{username}/chats", headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Ошибка получения чатов: {res.status_code}")
            return []
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")
        return []

def send_message(username: str, chat_id: str, message: str, files: Optional[List[str]] = None) -> str:
    if files is None:
        files = []
    
    data = {
        "username": username,
        "chat_id": chat_id,
        "message": message,
        "files": files
    }
    headers = {
        "X-Signature": generate_siganture(data),
        "X-Timestamp": str(int(time.time()))
    }
    try:
        resp = requests.post(f"{API_URL}/send/message", json=data, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            return f"Ошибка: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Ошибка подключения: {e}"

def get_chat_messages(username: str, chat_id: str):
    data = {
        "username": username,
        "chat_id": chat_id
    }
    headers = {
        "X-Signature": generate_siganture(data),
        "X-Timestamp": str(int(time.time()))
    }
    try:
        resp = requests.post(f"{API_URL}/get/chat/messages", json=data, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        st.error(f"Ошибка получения сообщений: {e}")
        return []

def delete_chat_api(username: str, chat_id: str) -> bool:
    data = {
        "username": username,
        "chat_id": chat_id
    }
    headers = {
        "X-Signature": generate_siganture(data),
        "X-Timestamp": str(int(time.time()))
    }
    try:
        resp = requests.post(f"{API_URL}/delete/chat", json=data, headers=headers)
        return resp.status_code == 200
    except Exception as e:
        st.error(f"Ошибка удаления чата: {e}")
        return False

# ========== ИНИЦИАЛИЗАЦИЯ СЕССИИ ==========

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_register' not in st.session_state:
    st.session_state.show_register = False 
if 'username' not in st.session_state:
    st.session_state.username = ""
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_chats" not in st.session_state:
    st.session_state.user_chats = []
if "chat_loaded" not in st.session_state:
    st.session_state.chat_loaded = False

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ЧАТАМИ ==========

def load_chat_history(chat_id: str):
    """Загружает историю сообщений для выбранного чата"""
    st.session_state.current_chat_id = chat_id
    messages = get_chat_messages(st.session_state.username, chat_id)
    
    # Преобразуем формат сообщений для Streamlit
    st.session_state.messages = []
    for msg in messages:
        role = "user" if msg.get("role") == "user" else "assistant"
        content = msg.get("message", "")
        st.session_state.messages.append({"role": role, "content": content})
    
    st.session_state.chat_loaded = True
    st.rerun()

def create_and_load_new_chat():
    """Создает новый чат и загружает его"""
    if create_new_chat(st.session_state.username):
        # Обновляем список чатов
        st.session_state.user_chats = get_user_chats(st.session_state.username)
        
        # Находим самый новый чат (последний в списке)
        if st.session_state.user_chats:
            new_chat = st.session_state.user_chats[-1]
            st.session_state.current_chat_id = new_chat["id"]
            st.session_state.messages = []
            st.session_state.chat_loaded = True
            st.rerun()
    else:
        st.error("Не удалось создать новый чат")

def get_chat_preview(messages: list) -> str:
    """Возвращает превью чата по первому сообщению"""
    if messages and len(messages) > 0:
        first_msg = messages[0].get("message", "")
        if len(first_msg) > 50:
            return first_msg[:47] + "..."
        return first_msg
    return "Новый чат"

# ========== СТРАНИЦА ЛОГИНА/РЕГИСТРАЦИИ ==========

if not st.session_state.logged_in:
    st.set_page_config(page_title="LawGPT - Вход", layout="centered")
    
    if st.session_state.show_register:
        st.title("📝 Регистрация")
        new_username = st.text_input("Имя пользователя", key="reg_user")
        new_password = st.text_input("Пароль", type="password", key="reg_pass1")
        confirm_password = st.text_input("Повторите пароль", type="password", key="reg_pass2")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Создать аккаунт", use_container_width=True):
                if not new_username or not new_password:
                    st.error("Заполните все поля.")
                elif new_password != confirm_password:
                    st.error("Пароли не совпадают.")       
                else:    
                    api_answer = register_api(new_username, new_password)
                    if not api_answer:
                        st.error("Это имя пользователя уже занято.")
                    else:    
                        st.success("Аккаунт успешно создан. Теперь вы можете войти.")
                        st.session_state.show_register = False
                        st.rerun()
        
        with col2:
            if st.button("← Назад ко входу", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()
    
    else:
        st.title("🔒 Вход в LawGPT")
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Войти", use_container_width=True):
                if login(username, hash_password(password)):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    # Загружаем чаты пользователя
                    st.session_state.user_chats = get_user_chats(username)
                    st.rerun()
                else:
                    st.error("Неверное имя пользователя или пароль")
        
        with col2:
            if st.button("Зарегистрироваться", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
    
    st.stop()

# ========== ОСНОВНОЙ ИНТЕРФЕЙС ЧАТА ==========

st.set_page_config(page_title="LawGPT", layout="wide")

# CSS для стилизации
st.markdown("""
<style>
    .stButton button {
        width: 100%;
    }
    .chat-preview {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .chat-preview:hover {
        background-color: #f0f2f6;
    }
    .chat-preview.active {
        background-color: #e6f3ff;
        border-left: 4px solid #1e88e5;
    }
    .delete-chat-btn {
        background-color: #ff4d4d;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 2px 8px;
        font-size: 12px;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# ========== САЙДБАР ==========

with st.sidebar:
    st.title(f"👤 {st.session_state.username}")
    
    # Кнопка нового чата
    if st.button("➕ Новый чат", use_container_width=True, type="primary"):
        create_and_load_new_chat()
    
    st.divider()
    
    # Список чатов
    st.subheader("📚 История чатов")
    
    # Обновляем список чатов
    st.session_state.user_chats = get_user_chats(st.session_state.username)
    
    if not st.session_state.user_chats:
        st.info("У вас пока нет чатов. Создайте первый!")
    else:
        for chat in st.session_state.user_chats:
            chat_id = chat.get("id", "")
            is_active = st.session_state.current_chat_id == chat_id
            
            # Создаем контейнер для превью чата
            col1, col2 = st.columns([4, 1])
            
            with col1:
                preview_text = get_chat_preview(chat.get("messages", []))
                if st.button(
                    preview_text,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    load_chat_history(chat_id)
            
            with col2:
                if st.button("🗑️", key=f"delete_{chat_id}", help="Удалить чат"):
                    if delete_chat_api(st.session_state.username, chat_id):
                        st.success("Чат удален")
                        st.session_state.user_chats = get_user_chats(st.session_state.username)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error("Не удалось удалить чат")

# ========== ОСНОВНАЯ ОБЛАСТЬ ЧАТА ==========

col1, col2 = st.columns([3, 1])
with col1:
    st.title("⚖️ LawGPT")
with col2:
    if st.button("Выйти", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.divider()

# Если чат не выбран
if not st.session_state.current_chat_id:
    st.info("👈 Выберите чат из списка слева или создайте новый")
    
    # Показываем инструкцию
    st.markdown("""
    ### Добро пожаловать в LawGPT!
    
    **LawGPT** - ваш умный помощник в юридических вопросах с 25-летним опытом.
    
    **Как пользоваться:**
    1. Выберите существующий чат из списка слева
    2. Или создайте новый чат, нажав кнопку "➕ Новый чат"
    3. Начните общение с вашим юристом-помощником
    
    **Возможности:**
    - Консультации по юридическим вопросам
    - Анализ документов
    - Объяснение законов и нормативных актов
    - Помощь в составлении документов
    """)
    
    st.stop()

# ========== ОТОБРАЖЕНИЕ СООБЩЕНИЙ ==========

# Показываем заголовок текущего чата
if st.session_state.current_chat_id:
    for chat in st.session_state.user_chats:
        if chat.get("id") == st.session_state.current_chat_id:
            preview = get_chat_preview(chat.get("messages", []))
            st.caption(f"📁 Текущий чат: {preview}")
            break

# Контейнер для сообщений
chat_container = st.container()

with chat_container:
    # Отображаем все сообщения
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ========== ВВОД СООБЩЕНИЯ ==========

if prompt := st.chat_input(f"Задайте вопрос LawGPT..."):
    # Проверяем, что выбран чат
    if not st.session_state.current_chat_id:
        st.error("Пожалуйста, выберите или создайте чат")
        st.stop()
    
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Отображаем сообщение пользователя
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Отображаем индикатор загрузки
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⚖️ Думаю...")
        
        # Отправляем сообщение и получаем ответ
        response = send_message(
            st.session_state.username,
            st.session_state.current_chat_id,
            prompt
        )
        
        # Отображаем ответ
        message_placeholder.markdown(response)
    
    # Добавляем ответ в историю
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Обновляем список чатов
    st.session_state.user_chats = get_user_chats(st.session_state.username)
    
    # Автоматически прокручиваем вниз
    st.rerun()