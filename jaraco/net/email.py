from __future__ import absolute_import

import re
import itertools
import email
import operator
import logging
import argparse
from imaplib import IMAP4_SSL
from getpass import getpass, getuser

import keyring

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_login_params(options):
	if not options.username:
		options.username = raw_input('username [%s]: ' % getuser()) or getuser()
	if not getattr(options, 'password', None):
		saved_password = keyring.get_password(options.hostname, options.username)
		options.password = (
			saved_password
			or getpass('password for %s: ' % options.username)
			)
		if options.save_password:
			keyring.set_password(options.hostname, options.username, options.password)

def add_arguments(parser):
	parser.add_argument('-u', '--username')
	parser.add_argument('--hostname', default='pod51011.outlook.com')
	parser.add_argument('--save-password', default=False, action="store_true")

def get_options():
	parser = argparse.ArgumentParser()
	add_arguments(parser)
	args = parser.parse_args()
	get_login_params(args)
	return args

class MessageDetailWrapper(object):
	"""
	Wrap an RFC822 message, but provide some extra attributes
	that are useful for determining sender details.
	"""
	def __init__(self, message):
		self._message = message
		self.refresh_detail()

	def refresh_detail(self):
		self._detail = self.get_sender_details(self._message)

	def __getattr__(self, name):
		if name == '__setstate__': raise AttributeError, name
		detail = self._detail and self._detail.get(name, None)
		return detail or getattr(self._message, name)

	@staticmethod
	def get_sender_details(message):
		def get_domain(hostname):
			return '.'.join(hostname.split('.')[-2:])

		def get_subnet(ip):
			octets = ip.split('.')
			octets[-1] = '0'
			return '.'.join(octets)+'/24'

		received_pat = re.compile('from (?P<name>.*) \(\[?(?P<sender>[0-9.]+)\]?\) by')
		if not 'Received' in message:
			log.warning('No Received header in message')
			return
		match = received_pat.match(message['Received'])
		if not match:
			log.warning('Unrecognized Received header: %s', message['Received'])
			return
		res = match.groupdict()
		res['domain'] = get_domain(res['name'])
		res['subnet'] = get_subnet(res['sender'])
		return res

def safe_attrgetter(attr):
	return lambda obj: getattr(obj, attr, None)

class MessageHandler(object):
	def __init__(self, options = None):
		self.options = options or get_options()

	def parse_imap_messages(self, messages):
		return itertools.imap(self.parse_imap_message, messages)

	@staticmethod
	def parse_imap_message(imap_item):
		typ, (data, flags) = imap_item
		id, msg = data
		msg = email.message_from_string(msg)
		msg = MessageDetailWrapper(msg)
		return msg

	def group_by(self, key):
		sorted_messages = sorted(self.messages, key=key)
		groups = itertools.groupby(sorted_messages, key)
		eval_groups = ((key, list(val)) for key, val in groups)
		return dict(eval_groups)

	@property
	def by_sender(self):
		key = safe_attrgetter('sender')
		return self.group_by(key)

	@property
	def by_domain(self):
		key = safe_attrgetter('domain')
		return self.group_by(key)

	@property
	def by_subnet(self):
		key = safe_attrgetter('subnet')
		return self.group_by(key)

	@staticmethod
	def largest_first(items):
		keys = items.keys()
		lengths = map(len, items.values())
		by_length = zip(lengths, keys)
		by_length.sort(reverse=True)
		swap = lambda (a,b): (b,a)
		return map(swap, by_length)

	def summarize(self):
		log.info('Parsed %d messages', len(self.messages))
		log.info(' from %d unique senders', len(self.by_sender))
		log.info(' on %d unique domains', len(self.by_domain))
		log.info(' on %d unique subnets', len(self.by_subnet))

	def get_folder_messages(self, folder, query='ALL', readonly=True):
		options = self.options
		get_login_params(options)
		self.server = IMAP4_SSL(options.hostname)
		self.server.login(options.username, options.password)
		self.server.select(folder, readonly=readonly)
		# for date-limited query, use 'SINCE "8-Aug-2006"'
		typ, data = self.server.search(None, query)
		self.message_ids = data[0].split()
		log.info('loading %d messages from %s', len(self.message_ids), folder)
		get_message = lambda id: self.server.fetch(id, '(BODY.PEEK[HEADER])')
		messages = itertools.imap(get_message, self.message_ids)
		return self.parse_imap_messages(messages)

class JunkEmailJanitor(MessageHandler):
	"""
	A MessageHandler that will go through the junk e-mail folder and
	remove messages sent by blocklisted servers.
	"""
	skip_messages_with_no_detail = False

	def run(self):
		self.messages = list(self.get_folder_messages('Junk E-mail', readonly=False))
		self.summarize()
		self.delete_messages_on_blocklist()

	def delete_messages_on_blocklist(self):
		from jaraco.net import dnsbl
		dnsbl_service = dnsbl.Service('zen.spamhouse.org')
		for id, msg in zip(self.message_ids, self.messages):
			if not msg._detail and self.skip_messages_with_no_detail: continue
			if msg._detail and not dnsbl_service.lookup(msg.sender): continue
			log.info('%s to be deleted', id)
			self.server.store(id, '+FLAGS', '\\Deleted')
		msg, deleted = self.server.expunge()
		deleted = filter(None, deleted)
		log.info('deleted %d messages', len(deleted))

def remove_known_spammers():
	global handler
	handler = JunkEmailJanitor()
	handler.run()
