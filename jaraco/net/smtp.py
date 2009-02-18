import socket, sys, re, time
from optparse import OptionParser

def _get_args():
	global options

	p = OptionParser()
	p.add_option('-p', '--port', type='int', help="Bind to port", default=25)

	options, args = p.parse_args()

import smtpd
import asyncore

class DebuggingServer(smtpd.DebuggingServer):
	def process_message(self, peer, mailfrom, rcpttos, data):
		# seriously, why doesn't a debugging server just print everything?
		for var, val in vars().items():
			if var in ('self', 'data'): continue
			print ': '.join(map(str, (var, val)))
		smtpd.DebuggingServer.process_message(self, peer, mailfrom, rcpttos, data)


def start_simple_server():
	"A simple mail server that sends a simple response"
	_get_args()
	addr = ('', options.port)
	s = DebuggingServer(addr, None)
	asyncore.loop()