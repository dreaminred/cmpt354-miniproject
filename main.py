import sqlite3
from os import path


conn = sqlite3.connect(path.join("notebooks", "library.db"))

user_id = None
user_type = None # User/Librarian

def main():
	print("# Library #")
	
	while (chk_conn(conn)):
		option = create_options_list("User signup", "User login", "Staff login", "Find an event", "Register for an event", "Exit")
		
		if option == 0:
			user_id = get_id_from_signup()
		elif option == 1:
			user_id = get_id_from_login(False)
		elif option == 2:
			user_id = get_id_from_login(True)
		elif option == 3:
			user_id = get_id_from_login(True)
		elif option == 4:
			user_id = get_id_from_login(True)
		else:
			conn.close()
			print("Database closed successfully.")

		

def get_id_from_signup():
	"""
	Ask user to sign up and return the unique id from a user.
	"""

	id = 0
	first_name = get_non_empty_string("Enter your first name: ", 30)
	last_name = get_non_empty_string("Enter your last name: ", 30)
	age = get_int("Enter your age: ", 7)

	with conn:
		cur = conn.cursor()

		myQuery = "INSERT INTO User(userID, firstName, lastName, age) VALUES(:newID, :newFirstName, :newLastName, :newAge)"
		while True:
			try:
				cur.execute(myQuery, {"newID":id, "newFirstName":first_name, "newLastName": last_name, "newAge": age})
				break;
			except sqlite3.IntegrityError:
				id = id + 1

	print("## New user created ##")
	print(f"{first_name} {last_name}. {age} years old.")
	print(f"*You may now log in using the user ID {id}*")

	return id


def get_id_from_login(is_librarian=False):
	"""
	Ask user/librarian for their respective ID
	"""
	if is_librarian:
		input_id = get_int('Enter LibrarianID: ', 0)

		cur = conn.cursor()

		nameQuery = "SELECT firstName, lastName FROM Librarian WHERE librarianID=:libID"

		cur.execute(nameQuery,{'libID':input_id})

		rows = cur.fetchall()

		if rows:
			print("Welcome!")
		else:
			print("LibrarianID not recognized.")


		for row in rows:
			print(row[1])
		print("\n")

	else:
		input_id = get_int('Enter UserID: ', 0)

	return -1

def create_options_list(*options):
	"""
	Create an enumerated list of options that the user can select from and
	return the selected value.

	Example
		create_options_list("option 1", "option 2")

		Result
			[0]: option 1
			[1]: option 2
		Select an option [0 - 1]: _______
	"""
	if len(options) <= 1:
		print("warning: options list should have more than 1 available option to select from")
		return 0

	for k, v in enumerate(options):
		print(f"[{k}]: {v}")

	options_size = len(options)
	selected = -1
	while (selected < 0) or (selected > (options_size - 1)):
		try:
			selected = int(input(f"Select an option [0-{options_size - 1}]: "))
		except ValueError:
			print("Invalid option.")
			continue

		if (selected < 0) or (selected > (options_size - 1)):
			print("Invalid option.")

	return selected

def get_non_empty_string(prompt, max_length):
	"""
	Get string from user input with prompt that ensures the string is

	- Not empty
	- And not exceeding the max_length
	"""
	string = input(prompt)
	while len(string.strip()) == 0 or len(string) > max_length:
		print(f"Invalid. Input string cannot be empty and must be <= {max_length}.")
		string = input(prompt)

	return string

def get_int(prompt, min):
	"""
	Get integer from user input and make sure it is >= min
	"""
	user_input = min - 1
	while user_input < min:
		try:
			user_input = int(input(prompt))
		except ValueError:
			print("Invalid integer.")
			continue

		if user_input < min:
			print(f"Invalid integer. Input must be >= {min}")

	return user_input

def chk_conn(conn):
     """
	 Checks whether conn is open or closed. Returns True/False if Open/Closed
	 """
     try:
        conn.cursor()
        return True
     except Exception as ex:
        return False


if __name__=='__main__':
	main()
