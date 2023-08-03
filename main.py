import sqlite3
import random
import datetime
from os import path


conn = sqlite3.connect("library.db")


def main():
	print("# Library #")

	user_id = None
	user_type = None # User/Librarian	

	while (chk_conn(conn)):

		print("\n")
		print_credentials(user_id, user_type)
		option = create_options_list("User signup", "User login", "Staff login", "Find an item", "Borrow an item", "Donate an item", "Find and register for events", "Volunteer", "Ask for help", "Return an Item", "Exit")

		if option == 0:
			user_id = get_id_from_signup() #Signup
		elif option == 1:
			user_id, user_type = get_id_from_login(False) # User login
		elif option == 2:
			user_id, user_type = get_id_from_login(True) # Staff login
		elif option == 3: # Finding an item
			find_item()
		elif option == 4: # Borrow an item
			borrow_item(user_id, user_type)
		elif option == 5: # Donate an item
			donate()
		elif option == 6:
			confirmation = find_events(user_id, user_type) # Find an event and return whether user wants to register for it
			if confirmation == True:
				print("Registered for event")
			else:
				print("Failed to register")
		elif option == 7:
			volunteer(user_id, user_type)
		elif option == 8:
			ask_for_help()
		elif option == 9:
			return_item(user_id, user_type)
		else:
			conn.close()
			print("Database closed successfully.")

def return_item(user_id, user_type):
	if user_id == None:
		print("Must be logged in")
		return

	if user_type != "User":
		print("You must be logged in as a user.")
		return

	# List out currently borrowed items
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT BorrowedItem.libraryItemID, itemName, author, dueDate FROM BorrowedItem NATURAL JOIN LibraryItem NATURAL JOIN Item WHERE userID=:id AND returnedDate IS NULL ORDER BY dueDate asc"
		cur.execute(sql_query, {'id': user_id})

		rows = cur.fetchall()
		print("\n### Currently borrowing ###\n")
		if rows:
			for row in rows:
				print(f"- [{row[0]}]: {row[1]} by {row[2]} DUE ON {row[3]}")
		else:
			print("---")
			return

	return_item_id = get_int("Enter id of item to return: ", 0)

	with conn:
		cur = conn.cursor()
		sql_query = "SELECT BorrowedItem.libraryItemID, userID, dueDate FROM BorrowedItem NATURAL JOIN LibraryItem WHERE BorrowedItem.libraryItemID=:libID AND userID=:userID AND dueDate IS NOT NULL AND returnedDate IS NULL"
		cur.execute(sql_query, {'libID': return_item_id, 'userID': user_id})

		row = cur.fetchone()

		if row:
			with conn:
				current_datetime = datetime.datetime.now()
				cur = conn.cursor()
				sql_query = f"UPDATE BorrowedItem SET returnedDate=:returned WHERE dueDate=:due AND libraryItemID=:libID AND userID=:userID"
				try:
					cur.execute(sql_query, {'returned': current_datetime, 'libID': row[0], 'userID': row[1], 'due': row[2]})
				except sqlite3.IntegrityError:
					print("Failed to return item")
					return
		else:
			print("Cannot return this item.")
			return

		print(f"Successfully returned item.")

def volunteer(user_id, user_type):
	if user_id == None:
		print("Must be logged in")
		return

	if user_type != "User":
		print("You must be logged in as a user.")
		return

	first_name = None
	last_name = None
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT firstName, lastName FROM User WHERE userID=:id"
		cur.execute(sql_query, {'id': user_id})

		row = cur.fetchone()

		first_name = row[0]
		last_name = row[1]

	id = 0
	with conn:
		cur = conn.cursor()
		sql_query = "INSERT INTO Librarian(librarianID, firstName, lastName, department) VALUES(:libID, :firstName, :lastName, :department)"

		while True:
			try:
				cur.execute(sql_query, {'libID': id, 'firstName': first_name, 'lastName': last_name, 'department': 'volunteer'})
				break;
			except sqlite3.IntegrityError:
				id = id + 1

	print(f"Success. You are now a volunteer and can log in as Staff using the id {id} in `Staff Login`")

def ask_for_help():
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT firstName, lastName, department FROM Librarian WHERE department <> \"volunteer\""
		cur.execute(sql_query)

		rows = cur.fetchall()
		index = random.randint(0, len(rows) - 1)
		print(f"\n{rows[index][0]} {rows[index][1]} ({rows[index][2]}) will be assisting you.")

def find_item():
	type_query = None
	while type_query != "movie" and type_query != "book" and type_query != "song" and type_query != "paper":
		type_query = get_non_empty_string("Type of item [book/movie/song/paper]: ", 30)
		if type_query != "book" and type_query != "movie" and type_query != "song" and type_query != "paper":
			print("Invalid type. Must be either \"book\", \"movie\", \"song\", \"paper\"")

	title_query = get_non_empty_string("Enter title: ", 30)
	author_query = get_non_empty_string("Enter author: ", 30)

	with conn:
		cur = conn.cursor()
		sql_query = "SELECT libraryItemID, itemName, author FROM LibraryItem NATURAL JOIN Item WHERE type=:type AND itemName=:title AND author=:author"
		cur.execute(sql_query, {'type':type_query, 'title':title_query, 'author':author_query})

		rows = cur.fetchall()

		print("\n")
		if rows:
			print("Found item (note: some of them may currently be borrowed out/pending to be included on shelf):")
			for row in rows:
				print(f"- (ID: {row[0]}) {row[1]} by {row[2]}")
		else:
			print("Item not in library")
		print("\n")

def borrow_item(user_id, user_type):
	if user_id == None:
		print("\nYou must be logged in to borrow items\n")
		return

	if user_type != 'User':
		print("\nYou must be logged into a user account to take out items\n")
		return

	# Get user profile
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT fines FROM User WHERE userID=:user_id"
		cur.execute(sql_query, {'user_id': user_id})
		row = cur.fetchone()

		if row:
			print(f"Total fines: $ {row[0]}")

			if row[0] > 0:
				print("You cannot borrow any items if you have fines.")
				return
		else:
			print("User does not exist (somehow)")
			return

	with conn:
		cur = conn.cursor()
		sql_query = "SELECT BorrowedItem.libraryItemID, itemName, author, dueDate FROM BorrowedItem NATURAL JOIN LibraryItem NATURAL JOIN Item WHERE userID=:userID AND returnedDate IS NULL"
		cur.execute(sql_query, {'userID': user_id})

		rows = cur.fetchall()

		print("### Currently borrowing ###")
		print("\n")
		if rows:
			for row in rows:
				print(f"- (ID: {row[0]}) {row[1]} by {row[2]} DUE {row[3]}")
		else:
			print("---")
		print("\n")

	type_query = None
	while type_query != "movie" and type_query != "book" and type_query != "song" and type_query != "paper":
		type_query = get_non_empty_string("Type of item [book/movie/song/paper]: ", 30)
		if type_query != "book" and type_query != "movie" and type_query != "song" and type_query != "paper":
			print("Invalid type. Must be either \"book\", \"movie\", \"song\", \"paper\"")

	title_query = get_non_empty_string("Enter title: ", 30)
	author_query = get_non_empty_string("Enter author: ", 30)

	# Search if the item exists
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT libraryItemID, itemName, author FROM LibraryItem NATURAL JOIN Item WHERE type=:type AND itemName=:title AND author=:author AND (toBeAdded IS NULL OR toBeAdded = 0)"
		cur.execute(sql_query, {'type':type_query, 'title':title_query, 'author':author_query})

		rows = cur.fetchall()

		if rows:
			with conn:
				cur = conn.cursor()
				sql_query = "SELECT libraryItemID FROM BorrowedItem WHERE libraryItemID=:id AND returnedDate IS NULL"
				cur.execute(sql_query, {'id': rows[0][0]})

				rowsBorrowed = cur.fetchall()

				if rowsBorrowed:
					print("No available item")
					return
				else:
					for row in rows:
						print(f"- (ID: {row[0]}) {row[1]} by {row[2]}")
		else:
			print("Sorry. Cannot find the item you're looking for.")
			return

	library_item_id = get_int("Enter item ID to borrow it: ", 0)

	# check if it is in BorrowedItem and if item has not been returned
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT itemName FROM BorrowedItem NATURAL JOIN LibraryItem NATURAL JOIN Item WHERE BorrowedItem.libraryItemID=:id AND returnedDate IS NULL"
		cur.execute(sql_query, {'id': library_item_id})

		rows = cur.fetchall()

		if rows:
			print("Sorry. Item not available to be taken out.")
			return

	# Take out the item
	with conn:
		cur = conn.cursor()
		sql_query = "SELECT itemName, author FROM LibraryItem NATURAL JOIN Item WHERE libraryItemID=:id"
		cur.execute(sql_query, {'id': library_item_id})

		row = cur.fetchone()

		if row:
			with conn:
				cur = conn.cursor()
				sql_query = "INSERT INTO BorrowedItem(userID, libraryItemID) VALUES(:user, :item)"
				try:
					cur.execute(sql_query, {'user': user_id, 'item': library_item_id})
				except sqlite3.IntegrityError:
					print("Sorry, you failed to take out this item.")
					return

			print(f"Successfully borrowed {row[0]} by {row[1]}.")
		else:
			print("Sorry. Invalid library item id.")
			return

def donate():
	type_query = None
	while type_query != "movie" and type_query != "book" and type_query != "song" and type_query != "paper":
		type_query = get_non_empty_string("Type of item [book/movie/song/paper]: ", 30)
		if type_query != "book" and type_query != "movie" and type_query != "song" and type_query != "paper":
			print("Invalid type. Must be either \"book\", \"movie\", \"song\", \"paper\"")

	title_query = get_non_empty_string("Enter title: ", 30)
	author_query = get_non_empty_string("Enter author: ", 30)

	# Add to Item
	item_id = 0
	with conn:
		cur = conn.cursor()

		sql_query = "INSERT INTO Item(itemID, author, itemName, type) VALUES (:id, :author, :itemName, :type)"
		while True:
			try:
				cur.execute(sql_query, {'id': item_id, 'author': author_query, 'itemName': title_query, 'type': type_query})
				break;
			except sqlite3.IntegrityError:
				item_id = item_id + 1

	# Add to LibraryItem
	library_item_id = 0
	with conn:
		cur = conn.cursor()

		sql_query = "INSERT INTO LibraryItem(libraryItemID, itemID) VALUES (:id, :item_id)"
		while True:
			try:
				cur.execute(sql_query, {'id': library_item_id, 'item_id': item_id})
				break;
			except sqlite3.IntegrityError:
				library_item_id = library_item_id + 1

	print("\n")
	print(f"Added \"{title_query}\" to library [id: {library_item_id}]")
	print("\n")

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
	Ask user/librarian for their respective ID. 
	Returns a tuple with their ID and respective ID type. 
	Returns 'Missing' for both if ID does not exist
	"""
	returnedID = 'Missing'
	returnedIDType = 'Missing'

	if is_librarian:
		input_id = get_int('Enter librarianID: ', 0)

		cur = conn.cursor()

		nameQuery = "SELECT firstName, lastName FROM Librarian WHERE librarianID=:libID"

		cur.execute(nameQuery,{'libID':input_id})

		rows = cur.fetchall()

		if rows:
			print("Welcome " + rows[0][0] + " " + rows[0][1] + "!")
			returnedID = input_id
			returnedIDType = 'Librarian'
		else:
			print("librarianID not recognized.")


	else:
		input_id = get_int('Enter userID: ', 0)

		cur = conn.cursor()

		nameQuery = "SELECT firstName, lastName FROM User WHERE userID=:usID"

		cur.execute(nameQuery,{'usID':input_id})

		rows = cur.fetchall()

		if rows:
			print("Welcome " + rows[0][0] + " " + rows[0][1] + "!")
			returnedID = input_id
			returnedIDType = 'User'
		else:
			print("userID not recognized.")

	return returnedID, returnedIDType


def print_credentials(id, idType):
	creds = [' ',' ']
	creds[0] = ('Missing') if (id == None) else id
	creds[1] = ('Missing') if (idType == None) else idType
	print('Credentials (userID, Type): ' + str(creds[0]) + '(' + str(creds[1]) +')')


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

	 Sourced from https://stackoverflow.com/questions/35368117/how-do-i-check-if-a-sqlite3-database-is-connected-in-python#:~:text=Create%20a%20boolean%20flag%20(say,set%20the%20flag%20to%20true.
	 """
	try:
		conn.cursor()
		return True
	except Exception as ex:
		 return False

def find_events(user_id='None', user_type='user'):
	"""
	Finds events and asks whether the user wants to register for them"""
	print("Filter by: ")
	user_option = create_options_list("By Room", "By Audience", "By Date Range") #Prompt user to input filter type
	attribute = ['room', 'audience']

	# Prompt user to input filter values
	if (user_option==0):
		input_user = get_non_empty_string("Enter targeted room:",4)
	elif (user_option==1):
		input_user = get_non_empty_string("Enter targeted audience:",10)
	elif (user_option==2):
		input_startTS = get_non_empty_string("Enter starting timestamp in ISO-8061 format (yyyy-mm-dd HH:MM):", 20)
		input_endTS = get_non_empty_string("Enter ending timestamp in ISO-8061 format (yyyy-mm-dd HH:MM):", 20)
	else:
		print("Invalid Entry: " + str(user_option))
		return False

	# Create the appropriate query 
	if ((user_option==0) or (user_option==1)):
		eventQuery = "SELECT * FROM Event WHERE " + attribute[user_option]+"=\""+input_user + "\""
	if ((user_option==2)):
		eventQuery = "SELECT * FROM Event WHERE " + "startTS" + " BETWEEN \"" + input_startTS + "\" AND \"" + input_endTS + "\""

	# Get rows
	with conn:
		cur = conn.cursor()
		try:
			cur.execute(eventQuery)
		except:
			print("Unable to execute query")

	rows = cur.fetchall()

	if(len(rows)==0):
		print("No events found.")
		return False

	# Display results
	for row, rowNum in zip(rows, range(len(rows))):
		rowString = ""
		for attrib in range(8):
			rowString += str(rowNum) + ". " + str(row[attrib]) + ", "
		print(rowString)
		
	# Prompt whether users wants to register for an event
	registrationOption = get_int("To register for an event, enter 1. \nTo go back to the main menu, enter 0.\n",0)
	if(registrationOption!=1):
		return False
	else:
		if(((user_id==None) or (user_id=='Missing')) or (user_type!='User')):
			print('You are not logged into a User account.')
			return False
	
	# Ask for the desired event for registration
	registrationOption2 = get_int("Enter the event number: ",0)
	startDate = rows[registrationOption2][0]
	room = rows[registrationOption2][2]

	# Attempt Registration
	with conn:
		cur = conn.cursor()

		sql_query = "INSERT INTO EventRegistration(startTS, room, userID) VALUES (:startTS, :room, :userID)"
		while True:
			try:
				cur.execute(sql_query, {'startTS': startDate, 'room': room, 'userID': user_id})
				return True
			except:
				return False

if __name__=='__main__':
	main()
