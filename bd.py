import mysql.connector
from mysql.connector import Error

conn = mysql.connector.connect(
    host='localhost',
    database='telegram-bot',
    user='root',
    password='',
    port=3307,
)
if conn.is_connected():
    print('Connected to MySQL database')

cursor = conn.cursor()

def save_mysql(text):
    cursor.execute(text)
    conn.commit()


def request_mysql(text, one=True):
    cursor.execute(text)
    if one:
        result = cursor.fetchone()
        if result:
            columns = [column[0] for column in cursor.description]
            result_dict = dict(zip(columns, result))
            return result_dict
    else:
        results = cursor.fetchall()
        if len(results):
            columns = [column[0] for column in cursor.description]
            results_dicts = [dict(zip(columns, result)) for result in results]
            return results_dicts
    return None


import logging
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
