import sqlite3

# Connect to the SQLite database (it will create the database file if it doesn't exist)
conn = sqlite3.connect('instance/meloverse_db.sqlite3')

# Create a cursor object to interact with the database
cursor = conn.cursor()

# # Create a table (if it doesn't exist)
cursor.execute("drop table creator")
conn.commit()

# # Insert data into the table
# cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)", ('john_doe', 'john@example.com'))


# # Commit the changes to the database
# conn.commit()

# Query data from the table
cursor.execute("SELECT * FROM user")
data = cursor.fetchall()

# Print the data
for row in data:
    print(row)

# Close the cursor and the database connection
cursor.close()
conn.close()
