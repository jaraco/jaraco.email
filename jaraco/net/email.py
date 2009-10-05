import re

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

		received_pat = re.compile('from (?P<name>.+) \(\[?(?P<sender>[0-9.]+)\]?\) by')
		if not 'Received' in message: return
		match = received_pat.match(message['Received'])
		if not match: return
		res = match.groupdict()
		res['domain'] = get_domain(res['name'])
		res['subnet'] = get_subnet(res['sender'])
		return res

