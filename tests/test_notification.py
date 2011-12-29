from jaraco.net import notification

class TestMailbox(object):
	def test_dest_addrs(self):
		mbx = notification.SMTPMailbox(
			to_addrs = "a@example.com,b@example.com",
			cc_addrs = "c@example.com,d@example.com",
			bcc_addrs = "e@example.com,f@example.com",
		)
		assert len(mbx.dest_addrs) == 6
