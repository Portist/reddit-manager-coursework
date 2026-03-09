"""
Точка входа (Entry Point) приложения.
Выполняет первичную инициализацию слоя данных и запускает цикл отрисовки пользовательского интерфейса.
Запуск осуществляется командой: streamlit run main.py
"""
from app.ui.main_page import render_page
from app.db.crud import init_db

# Инициализация схемы реляционной базы данных.
# Вызов безопасен при каждом rerun Streamlit, так как SQLAlchemy (create_all)
# под капотом использует конструкцию 'CREATE TABLE IF NOT EXISTS'.
init_db()

if __name__ == "__main__":
    # Делегирование управления слою представления
    render_page()