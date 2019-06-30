# kontess-back-end

## To run
Install requirements  
`pip install -r requirements.txt `  
(I might of forgotten something, if you crash add it or raise an issue)

Run server
`python manage.py runserver`

Runs on localhost:8000

If got unapplied migration warnings when running server, quit server first;

Then run `python manage.py migrate`

##  Admin
Go to web browser, Localhost:8000/admin  
Username = ***REMOVED_USER***  
Password = ***REMOVED_PASSWORD***  

Make a new SuperUser  
`python manage.py createsuperuser`

## Documentation
Look at PostMan requests for examples  

[Users](#Users)  
**POST /user/users/**  
create user
```
PARAMS:
"first_name"                : String # required
"last_name"                 : String # required
"username"                  : Email required
"password"                  : String # required

RETURNS:
"user data with token"      : JSON
```

**POST /token-auth/**  
create user token
```
PARAMS:
"username"                  : Email required
"password"                  : String # required

RETURNS:
"competition"               : JSON
```


**GET /current_user/**  
get user by token
```
HEADERS:
"Authorization"             : JWT string, JWT $(token)
RETURNS:
"user data"                 : JSON
```
