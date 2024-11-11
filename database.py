import sqlite3

def init_db():
    """Initializes the SQLite database and creates the 'tools' table if it doesn't exist."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tools (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        description TEXT,
                        instructions TEXT,
                        link TEXT
                     )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_history (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        request_type TEXT NOT NULL,
                        request_content TEXT,
                        response_content TEXT,
                        image_url TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()

def add_tool(name, category, description, instructions):
    """Adds a new tool to the 'tools' table."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tools (name, category, description, instructions) VALUES (?, ?, ?, ?)",
                   (name, category, description, instructions))
    conn.commit()
    conn.close()

def get_tool_by_category(query):
    """Fetches tools from the 'tools' table based on a search query in category or description."""
    conn = sqlite3.connect("ai_tools.db")  # Use the correct database file name
    cursor = conn.cursor()
    
    # Search for tools matching the category or description
    cursor.execute("SELECT * FROM tools WHERE category LIKE ? OR description LIKE ?", (f"%{query}%", f"%{query}%"))
    tools = cursor.fetchall()
    
    # Close the database connection
    conn.close()
    
    return tools

def delete_tool(tool_id):
    """Deletes a tool from the 'tools' table based on the provided tool ID."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
    conn.commit()
    conn.close()

def save_user_history(user_id, request_type, request_content, response_content, image_url=None):
    """Сохраняет запрос пользователя, ответ бота и, при наличии, ссылку на изображение в таблицу 'user_history'."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_history (user_id, request_type, request_content, response_content, image_url) VALUES (?, ?, ?, ?, ?)",
        (user_id, request_type, request_content, response_content, image_url)
    )
    conn.commit()
    conn.close()
    
def get_user_history(user_id):
    """Получает историю запросов и ответов для данного пользователя из таблицы 'user_history'."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT request_type, request_content, response_content, image_url, timestamp "
        "FROM user_history WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,)
    )
    history = cursor.fetchall()
    conn.close()
    return history


