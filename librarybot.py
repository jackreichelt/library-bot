from time import sleep
from slackclient import SlackClient
import os
from datetime import datetime
from library import *
from pytz import timezone
import atexit
from tinys3 import Connection

NAME = 'library_bot'

posted = False

@atexit.register
def save_library():
  print('Writing library.')
  lib.write_library()
  conn.upload('borrowers.txt', open('borrowers.txt', 'rb'), 'iit-library')

usage = """
Welcome to the IIT Library!

You can checkout a book like this. Supplying a username will borrow it for that person.
`libcheckout <book name> [@<username>]`
You can return a book like this. Supplying a username will return it for that person.
`libcheckin <book name> [@<username>]`
You can see a list of all borrowed books like this. This will also happen once a week automatically
`library`

Anything else and I'll show you this message to help you out!

If you have any facts you want to add, comments, complaints, or bug reports, message Jack Reichelt.
"""

TOKEN = os.environ.get('TOKEN', None) # found at https://api.slack.com/web#authentication
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', None)
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', None)

conn = Connection(S3_ACCESS_KEY, S3_SECRET_KEY, endpoint='s3-ap-southeast-2.amazonaws.com')

saved_subs = conn.get('borrowers.txt', 'iit-library')

f = open('borrowers.txt', 'wb')
f.write(saved_subs.content)
f.close()

lib = Library()

sc = SlackClient(TOKEN)
if sc.rtm_connect() == True:
  print('Connected.')

  sc.api_call("im.list")

  while True:
    response = sc.rtm_read()
    for part in response:
      print(part)
      if 'ims' in part:
        channels = part['ims']
      if part['type'] == 'message' and 'text' in part:
        words = part['text'].split()

        # Borrowing a book for another user
        if words[0] == 'libcheckout' and words[-1].startswith('<@'):
          user = sc.server.users.find(words[-1][2:-1])
          if user == None:
            sc.api_call("chat.postMessage", channel=part['channel'], text="That user doesn't exist. Try tagging them with @.", username=NAME, icon_emoji=':book:')
          else:
            user_id = user.id
            username = user.real_name
            lib.borrow_book(user_id, username, ' '.join(words[1:-1]))
            sc.api_call("chat.postMessage", channel=part['channel'], text="{} has borrowed {}.".format(username, ' '.join(words[1:-1])), username=NAME, icon_emoji=':book:')

        # Borrowing a book for themselves
        elif words[0] == 'libcheckout':
          user_id = part['user']
          username = sc.api_call("users.info", user=user_id)['user']['profile']['real_name']

          lib.borrow_book(user_id, username, ' '.join(words[1:]))
          sc.api_call("chat.postMessage", channel=part['channel'], text="{} has borrowed {}.".format(username, ' '.join(words[1:])), username=NAME, icon_emoji=':book:')

        # Returning a book for another user
        elif words[0] == 'libcheckin' and words[-1].startswith('<@'):
          lib_response = lib.return_book(words[-1][2:-1], ' '.join(words[1:-1]))

          if lib_response == -1:
            sc.api_call("chat.postMessage", channel=part['channel'], text="That user doesn't have any books borrowed.", username=NAME, icon_emoji=':book:')
          elif lib_response == -2:
            sc.api_call("chat.postMessage", channel=part['channel'], text="That user hasn't borrowed that book.", username=NAME, icon_emoji=':book:')
          else:
            sc.api_call("chat.postMessage", channel=part['channel'], text="{} has been returned.".format(words[1:-1]), username=NAME, icon_emoji=':book:')

        # Returning a book for themselves
        elif words[0] == 'libcheckin':
          lib_response = lib.return_book(part['user'], ' '.join(words[1:]))

          if lib_response == -1:
            sc.api_call("chat.postMessage", channel=part['channel'], text="You don't have any books borrowed.", username=NAME, icon_emoji=':book:')
          elif lib_response == -2:
            sc.api_call("chat.postMessage", channel=part['channel'], text="You haven't borrowed that book.", username=NAME, icon_emoji=':book:')
          else:
            sc.api_call("chat.postMessage", channel=part['channel'], text="{} has been returned.".format(words[1:-1]), username=NAME, icon_emoji=':book:')

        elif len(words) == 1 and words[0] == 'library':
          if lib.count():
            sc.api_call("chat.postMessage", channel=part['channel'], text=lib.all_borrowed_books(), username=NAME, icon_emoji=':book:')
          else:
            sc.api_call("chat.postMessage", channel=part['channel'], text='There are no borrowed books.', username=NAME, icon_emoji=':book:')

        elif ('library' in words and 'help' in words) or 'libraryhelp' in words:
          sc.api_call("chat.postMessage", channel=part['channel'], text=usage, username=NAME, icon_emoji=':book:')

        save_library()

    # bookclub channel is C0QPDRHD2
    if 0 <= datetime.now(timezone('Australia/Sydney')).time().hour < 1 and posted == True: #midnight to 1am
      print('It\'s a new day.')
      posted = False
    if 9 <= datetime.now(timezone('Australia/Sydney')).time().hour < 10 and posted == False and datetime.now(timezone('Australia/Sydney')).weekday() == 3: #3pm to 5pm
      print('It\'s cat fact time!')
      posted = True
      sc.api_call("chat.postMessage", channel='C0QPDRHD2', text=lib.all_borrowed_books(), username=NAME, icon_emoji=':book:')

    sleep(1)
else:
  print('Connection Failed, invalid token?')