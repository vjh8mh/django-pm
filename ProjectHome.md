This is a functional work in progress for a private message system for Django projects.

The folders are accessed through the user's related manager:
  * user.inbox for received messages
  * user.outbox for sent messages
  * user.drafts for saved messages

## Features: ##
  * Contact list
  * Black list
  * User filter in the message lists
  * Undelete
  * Message history

Check out the urls and the models to have a better idea:
  * http://django-pm.googlecode.com/svn/trunk/myproject/pm/urls.py
  * http://django-pm.googlecode.com/svn/trunk/myproject/pm/models.py

## TODO: ##
  * clean some logic
  * fixtures and css for the project example
  * templates internationalization
  * French locale ( because i can :P )
  * cron script to remove messages flagged for deletion
  * unit tests ( yeah, i know, i should have done them before ! :P )

## Project example: ##
In the trunk you will find a test project, download it and run
```
manage.py runserver
```
Go to the admin url http://127.0.0.1:8000/admin/ and log in with "Admin" / "test" ( case sensitive )

Then go to your inbox : http://127.0.0.1:8000/pm/inbox/

You can only send messages to yourself in this project

## Notification: ##
The private messaging system gives a feedback to the user through a custom system using the sessions framework.

You can either use it for your whole project, or replace it in the code with
```
request.user.messages_set.create(message=message)
```
There is a special caveat with the messages containing undo links when you delete a message.

This notification system is explained here :
http://django-pm.googlecode.com/svn/trunk/myproject/notification/__init__.py

## User input filtering: ##
User input is not filtered but the hooks are there, feel free to add your recipies there:
http://django-pm.googlecode.com/svn/trunk/myproject/pm/formatters.py

## Trunk: ##

http://django-pm.googlecode.com/svn/trunk/