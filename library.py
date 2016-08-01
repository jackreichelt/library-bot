from datetime import datetime
from pytz import timezone

class Library(object):

  users = {} #format: {user id: user object}

  def __init__(self):
    subs = open('borrowers.txt')
    for line in subs:
      chunks = line.split(',')

      user_details = chunks[0].split(':')
      users[user_details[0]] = User(user_details[1])

      for book in chunks[1:]:
        title,date = book.rsplit(':',1)
        self.borrow_book(user_details[0], user_details[1], title, date)

  def borrow_book(self, user_id, user_name, book, date = None):
    if user_id not in self.users:
      self.users[user_id] = User(user_name)

    self.users[user_id].borrow_book(book, date)

  def return_book(self, user_id, book):
    if user_id not in self.users:
      return -1

    if self.users[user_id].return_book(book) == -2:
      return -2

  def all_borrowed_books(self):
    out = ''

    for user_id, user in self.users.items():
      if user.count() > 0:
        out += '<@{}> has borrowed:\n{}\n'.format(user_id, user.list_books())

    return out

  def count(self):
    total = 0

    for user in self.users.values():
      total += user.count()

    return total

  def write_library(self):
    f = open('borrowers.txt')

    for user_id, user in self.users.items():
      if user.count() > 0:
        f.write('{}:{}'.format(user_id, user.write_user()))

class User(object):

  name = ''
  borrowed_books = {}

  def __init__(self, name):
    self.name = name
    self.borrowed_books = {}

  def borrow_book(self, book, date = None):
    if book in self.borrowed_books:
      return -1

    if date == None:
      self.borrowed_books[book] = datetime.now(timezone('Australia/Sydney')).date()
    else:
      self.borrowed_books[book] = datetime.strptime(date, '%Y/%m/%d').date() #format is yyyy/mm/dd, e.g. 2016/04/15, for April 15th, 2016.

  def return_book(self, book):
    if book not in self.borrowed_books:
      return -2

    self.borrowed_books.pop(book)

  def list_books(self):
    out = ''
    current_date = datetime.now(timezone('Australia/Sydney')).date()

    for book, date in self.borrowed_books.items():
      out += '    {}, borrowed {} days ago.\n'.format(book, (current_date-date).days)

    return out

  def count(self):
    return len(self.borrowed_books)

  def write_user(self):
    out = '{}'.format(self.name)

    for book, date in self.borrowed_books.items():
      out += ',{}:{}'.format(book, datetime.strftime(date, '%Y/%m/%d'))

    return out
