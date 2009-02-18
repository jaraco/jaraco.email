# -*- coding: UTF-8 -*-

"""Notifiers
	Classes for notifying in the case of an event.

	All objects should support the .write method to append data and
	.Notify to send the message.

	Objects:
		SMTPMailbox - sends a message to an SMTP mailbox upon
			notification.
			
Copyright © 2004-2008 Jason R. Coombs
"""

__author__ = 'Jason R. Coombs <jaraco@jaraco.com>'
__version__ = '$Revision$a'[11:-2]
__svnauthor__ = '$Author$'[9:-2]
__date__ = '$Date$'[7:-2]

import string
import smtplib
import socket
import sys
import traceback
from StringIO import StringIO

from jaraco.util.dictlib import DictFilter
from jaraco.util.iter_ import flatten

class NotificationTarget(object):
	def write(self, msg):
		self.notify(msg)

class SMTPMailbox(NotificationTarget):
	from_addr = None

	def __init__(self, to_addrs, **kwargs):
		kwargs['to_addrs'] = to_addrs
		self.__dict__.update(kwargs)
		if self.from_addr is None:
			self.from_addr = self.get_generic_from_addr()

	@classmethod
	def get_generic_from_addr(cls):
		import socket
		machine_name = socket.getfqdn()
		class_name = cls.__name__
		return '%(class_name)s <notifier@%(machine_name)s>' % vars()

	def notify(self, msg = '', importance = 'Normal', subject='Notification'):        
		import smtplib

		headers = dict(
			From = self.from_addr,
			To = self.to_addrs,
			Importance = importance,
			Subject = subject,
			)

		if hasattr(self, 'cc_addrs'):
			headers['CC'] = self.cc_addrs

		smtp_args = self.get_connect_args()
		server = smtplib.SMTP(**smtp_args)
		server.sendmail(
			self.from_addr,
			self.dest_addrs,
			self.format_message(headers, msg))
		server.quit()

	@property
	def dest_addrs(self):
		from string import strip
		get_attr = lambda a: getattr(self, a, None)
		to_attrs = ('to_addrs', 'cc_addrs', 'bcc_addrs')
		values = filter(None, map(get_attr, to_attrs))
		split_email = lambda s: map(strip, s.split(','))
		all_addrs = flatten(map(split_email, values))
		return all_addrs

	def get_connect_args(self):
		attrs = 'host', 'port'
		return dict(DictFilter(self.__dict__, attrs))

	@staticmethod
	def format_message(headers, msg):
		msg = msg.encode('ascii', 'replace')
		format_header = lambda h: '%s: %s\n' % h
		formatted_headers = map(format_header, headers.items())
		header = ''.join(formatted_headers)
		return '\n'.join((header, msg))

	def __repr__(self):
		return 'mailto:' + self.to_addrs

class BufferedNotifier(NotificationTarget):
	"""
	Just like a regular notifier, but Notify won't be called until
	.flush() is called or this object is destroyed.
	"""
	def write(self, partial):
		self._get_buffer().write(partial)

	def flush(self):
		msg = self._get_buffer().getvalue()
		# don't send an empty message
		if msg:
			self.notify(msg)
		
	def _get_buffer(self):
		return self.__dict__.setdefault('buffer', StringIO())

	def __del__(self):
		# note, the documentation warns against performing external
		#  varying code in the destructor, and since flush calls
		#  Notify, this call is arbitrarily complex and varying.
		#  However, this appears to be the only way to guarantee
		#  that the notification is actually sent.
		self.flush()
		
class ExceptionNotifier(BufferedNotifier, SMTPMailbox):
	"""
	Wrap a function or method call with an exception handler
	that will send an SMTP message if an exception is caught.
	"""
	def __init__(self, target_func, *args, **kargs):
		super(ExceptionNotifier, self).__init__(*args, **kargs)
		self.target_func = target_func

	def __call__(self, *args, **kargs):
		try:
			return self.target_func(*args, **kargs)
		except Exception, e:
			print >> self, 'Unhandled exception encountered'
			traceback.print_exc(file=self)
			self.flush()
			raise
