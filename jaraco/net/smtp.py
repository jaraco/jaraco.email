import socket
import sys
import re
import time
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
		for var, val in vars().items():
			if var in ('self', 'data'): continue
			print ': '.join(map(str, (var, val)))
		smtpd.DebuggingServer.process_message(self, peer, mailfrom, rcpttos, data)

def start_simple_server():
	"A simple mail server that sends a simple response"
	args = _get_args()
	addr = ('', args.port)
	s = DebuggingServer(addr, None)
	asyncore.loop()
