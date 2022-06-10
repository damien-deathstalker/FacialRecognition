import sqlite3, logging
from datetime import datetime
from pathlib import PurePath
from . import FILE_PATH, SYSTEM_LOGS

logger = logging.getLogger('sqlite_handler')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(PurePath(SYSTEM_LOGS, 'sqlite_handler_err.log'), mode='a+')
logger.addHandler(file_handler)

DATABASE_PATH = PurePath(FILE_PATH, 'db.sqlite3')

SQL_STATEMENTS = dict(
	CREATE_TABLE_STATEMENT = """
	CREATE TABLE facial_records (
		id INTEGER PRIMARY KEY,
		staff_id_id TEXT NOT NULL,
		date TEXT NOT NULL,
		clock_in TEXT,
		clock_out TEXT
	);
	""", 
	INSERT_STATEMENT = "INSERT INTO facial_records (staff_id_id, date, clock_in) VALUES (?, ?, ?);",
	UPDATE_STATEMENT = "UPDATE facial_records SET clock_out = ? WHERE staff_id_id = ? AND date = ?;",
	FETCH_NAME = "SELECT short_name from employees_employee WHERE staff_id = ?;",
)

def open_db(require_cursor:bool = False):
	"""
	Opens a sqlite3 connection to the database.
	require_cursor:\tDefault False. Set to True if cursor is required
	"""
	connection = sqlite3.connect(DATABASE_PATH)
	if require_cursor:
		cursor = connection.cursor()
		return connection, cursor
	return connection

def close_db(connection:sqlite3.Connection):
	"""
	Accepts a connection and closes it.
	"""
	connection.close()
	return

def initialize_database():
	"""
	Initialize the Databse by creating the Table
	"""
	connection = open_db()
	with connection:
		connection.execute(SQL_STATEMENTS['CREATE_TABLE_STATEMENT'])
	close_db(connection)
	return "Database Initialised"

def clock_in_insert(name:str, time:datetime):
	"""
	Inserts a clock_in record in the database.
	name:\tName of clocking in individual
	time:\tTime recorded.
	"""
	try:
		name = name.strip()
		date = time.date().isoformat()
		clock_in = time.time().isoformat()
		connection = open_db()
		with connection:
			connection.execute(SQL_STATEMENTS['INSERT_STATEMENT'], (name, date, clock_in))
	except: 
		logger.exception(f"Clock-in for {name} @ {datetime.now().isoformat()}")
	close_db(connection)
	return

def clock_out_update(name:str, time:datetime):
	"""
	Updates a clock_in record in the database with the clock_out time.
	name:\tName of clocking out individual
	time:\tTime recorded.
	"""
	try:
		name = name.strip()
		date = time.date().isoformat()
		clock_out = time.time().isoformat()
		connection = open_db()
		with connection:
			connection.execute(SQL_STATEMENTS['UPDATE_STATEMENT'], (clock_out, name, date))
	except:
		logger.exception(f"Clock-out for {name} @ {datetime.now().isoformat()}")
	close_db(connection)
	return
	
def fetch_name(name:str):
	data = [("Person",)]
	try:
		name = name.strip()
		connection = open_db()
		with connection:
			cursor = connection.execute(SQL_STATEMENTS['FETCH_NAME'], (name, ))
			data = cursor.fetchall()
	except:
		logger.exception(f"Clock-out for {name} @ {datetime.now().isoformat()}")
	close_db(connection)
	if data.count == 0:
		data = [("Person",)]
	return str(data[0][0]).title()
