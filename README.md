# kontess-back-end

## To run

Install requirements  
`pip install -r requirements.txt`  
(I might of forgotten something, if you crash add it or raise an issue)

Run server
`python manage.py runserver`

Runs on localhost:8000/api

If got unapplied migration warnings when running server, quit server first;

Then run `python manage.py migrate`

## Admin

Go to web browser, Localhost:8000/admin  
Username = ***REMOVED_USER***  
Password = ***REMOVED_PASSWORD***

Make a new SuperUser  
`python manage.py createsuperuser`

## Documentation

Look at PostMan requests for examples
Link: localhost:8000/api/

[Token](#Tokens)
[Participants](#Participants)  
[Organizer](#Organizer)
[Team](#Teams)

### Tokens

JWT Tokens need to be provided in Header for CUD actions
Authorization: Bearer `token`

**POST /token/**  
get JWT token for user

```
PARAMS:
"username"                  : String # required
"password"                  : String # required

RETURNS:
"access token"              : String
"refresh token"             : String
```

**POST /token/refresh/**
refreshes access token without needing password

```
PARAMS:
"refresh token"             : String # required

RETURNS:
"access token"              : String
"refresh token"             : String
```

### Participants

Participant Requests

**GET /participant/**
list participants

```
RETURNS:
"participant info"          : JSON Object
```

**GET /participant/id/**
get participant

```
RETURNS:
"participant info"          : JSON Object
```

**POST /participant/**  
create participant

```
PARAMS:
"username"                  : String # required
"password"                  : String # required
"first_name"                : String # required
"last_name"                 : String # required
"graduation_year"           : String # required

RETURNS:
"participant info"          : JSON Object
```

**POST /participant/login**  
authenticate participant since authorization is token based not session

```
PARAMS:
"username"                  : String # required
"password"                  : String # required

RETURNS:
"status"                    : JSON Object
```

**POST /participant/id/create_team_request**
create a participant join request

```
PARAMS:
"teamId"                    : Int required
"essay"                     : String # required, max 100 characters

RETURNS:
"team request object"       : JSON object
```

### Organizer

Organizer Requests

**GET /organizer/**
list organizers

```
RETURNS:
"organizer info"            : JSON Object
```

**GET /organizer/id/**
get organizer

```
RETURNS:
"organizer info"            : JSON Object
```

**POST /organizer/**  
create organizer

```
PARAMS:
"username"                  : String # required
"password"                  : String # required
"first_name"                : String # required
"last_name"                 : String # required
"title"                     : String # required

RETURNS:
"organizer info"            : JSON Object
```

**POST /organizer/login**  
authenticate organizer since authorization is token based not session

```
PARAMS:
"username"                  : String # required
"password"                  : String # required

RETURNS:
"status"                    : JSON Object
```

### Team

Team requests

**POST /team/**  
Create team

```
PARAMS:
"name"                      : String # required
"description"               : String # required

RETURNS:
"access token"              : String
"refresh token"             : String
```

**GET /team/id/**
get specific team

```
RETURNS:
"team"                      : JSON object
```

**GET /team/**
list teams

```
RETURNS:
"teams"                     : JSON object
```

**POST /team/id/accept_team_request**
list teams

```
PARAMS:
"requestId"                 : Int required

RETURNS:
"status"                    : JSON Object
```

**DELETE /team/id/reject_team_request**
list teams

```
PARAMS:
"requestId"                 : Int required

RETURNS:
"status"                    : JSON Object
```
