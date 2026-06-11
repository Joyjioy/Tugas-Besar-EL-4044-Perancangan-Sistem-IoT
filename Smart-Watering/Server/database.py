import sqlite3

DB_NAME = "db.sqlite"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS soil_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        soil INTEGER,
        pump TEXT,
        humidity INTEGER,
        temperature REAL,
        rain INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_history(
    soil,
    pump,
    humidity,
    temperature,
    rain
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO soil_history (
        soil,
        pump,
        humidity,
        temperature,
        rain
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        soil,
        pump,
        humidity,
        temperature,
        int(rain)
    ))

    conn.commit()
    conn.close()


def get_history(limit=50):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT
        soil,
        pump,
        humidity,
        temperature,
        rain,
        created_at
    FROM soil_history
    ORDER BY id DESC
    LIMIT {limit}
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows
