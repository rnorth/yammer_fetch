"""
	NAME
		yammer_fetch.py
	
	SYNOPSIS
		python yammer_fetch.py
	
	DESCRIPTION
		This script fetches all of a specific user's Yammer posts.
		
"""
import urllib
import urllib2
import json
import time
import getpass
import ConfigParser
from os import path
from BeautifulSoup import BeautifulSoup
import keyring

class HttpBot:
	"""
	An HttpBot represents one browser session, with cookies. 
	Stolen from http://stackoverflow.com/a/4836113/72305
	"""
	def __init__(self):
		cookie_handler= urllib2.HTTPCookieProcessor()
		redirect_handler= urllib2.HTTPRedirectHandler()
		self._opener = urllib2.build_opener(redirect_handler, cookie_handler)
	
	def GET(self, url):
		return self._opener.open(url).read()
	
	def POST(self, url, parameters):
		return self._opener.open(url, urllib.urlencode(parameters)).read()

def get_settings():
	"""Return user-specific settings for this script"""
	# config file init
	config_file = path.expanduser('~/.yammer_fetch.cfg')
	print "Settings for this script will be referenced from %s" % config_file
	
	config = ConfigParser.SafeConfigParser()
	config.read(config_file)
	if not config.has_section('login'):
		config.add_section('login')
	if not config.has_section('yammer'):
		config.add_section('yammer')
	
	try:
		username = config.get('login','username')
		user_id = config.get('yammer','user_id')
	except ConfigParser.NoOptionError:
		username = raw_input("Username: ")
		user_id = raw_input("Yammer User ID: ")
		
	# store the username and user ID
	config.set('login', 'username', username)
	config.set('yammer', 'user_id', user_id)
	config.write(open(config_file, 'w'))	
	
	password = None
	password = keyring.get_password('yammer_fetch', username)
	
	if password == None:
		password = getpass.getpass("Password: ")
		
		# store the password
		try:
			keyring.set_password('yammer_fetch', username, password)
		except keyring.backend.PasswordSetError:
			print "Failed to store password in system secure keyring - not storing"
	
	# the stuff that needs authorization here
	return (username, password, user_id)

if __name__ == "__main__":
	
	(username, password, user_id) = get_settings()
	
	bot = HttpBot()
	print "Logging in to Yammer..."
	login_page = bot.GET("https://www.yammer.com/login")
	auth_token = BeautifulSoup(login_page).find("input", {"name":"authenticity_token"})["value"]
	bot.POST('https://www.yammer.com/session', {'login':username, 'password':password, 'authenticity_token':auth_token})
	
	# A big number so that we start at the most recent posts
	oldest_found = 9999999999
	print "Fetching articles by user ID %s" % user_id
	while True:
		# print "Looking for messages older than %s" % oldest_found
		messages = json.loads( bot.GET("https://www.yammer.com/api/v1/messages/from_user/%s.json?older_than=%d" % (user_id, oldest_found)) )
		if len(messages['messages']) == 0:
			# No more messages
			break
		
		for message in messages['messages']:
			oldest_found = min(oldest_found, int(message['id']))
			print "\n\n---"
			print "id: %s" % message['id']
			print "date: %s" % message['created_at']
			print ""
			print message['body']['plain'].encode('utf8')
			
		time.sleep(5)
	
	print "All articles fetched"
