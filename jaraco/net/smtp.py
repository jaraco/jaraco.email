from __future__ import print_function, unicode_literals

import smtpd
import asyncore
import argparse

def _get_args():
	p = argparse.ArgumentParser()
	p.add_argument('-p', '--port', type=int, help="Bind to port",
		default=25)
	return p.parse_args()

class DebuggingServer(smtpd.DebuggingServer):
	def process_message(self, peer, mailfrom, rcpttos, data):
		# seriously, why doesn't a debugging server just print everything?
		print('peer:', peer)
		print('mailfrom:', mailfrom)
		print('rcpttos:', rcpttos)
		smtpd.DebuggingServer.process_message(self, peer, mailfrom, rcpttos, data)

def start_simple_server():
	"A simple mail server that sends a simple response"
	args = _get_args()
	addr = ('', args.port)
	s = DebuggingServer(addr, None)
	asyncore.loop()
