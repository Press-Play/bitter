
Username Rules
--------------
	- 	Must only contain a-z, or numbers 0-9.
	- 	Can choose lower or uppercase letters, but only the lowercase
		version will be stored as a unique identifier.
	-	Must be at least 4 characters long.

Email Rules
--------------
	-	For now allow users to have multiple accounts under the same email.
	-	TODO: Check if an email exists; make unique identifier

Password Rules
--------------
	-	Must be at least 5 characters long.
	-	Can contain any mixture of letters and numbers.
	-	Special characters not allowed.

Development
--------------
    - Run a local server `python3 -m http.server --cgi` from root directory.
    - Ensure CGI script is in `/cgi-bin`.
    - Go to `http://0.0.0.0:8000/cgi-bin/bitter.cgi`.
    - Push code to `master`and it is deployed automatically via Heroku.