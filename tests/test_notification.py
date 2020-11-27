from unittest import mock
from jaraco.email import notification


class TestMailbox(object):
    def test_dest_addrs(self):
        mbx = notification.SMTPMailbox(
            to_addrs="a@example.com,b@example.com",
            cc_addrs="c@example.com,d@example.com",
            bcc_addrs="e@example.com,f@example.com",
        )
        assert len(mbx.dest_addrs) == 6

    @mock.patch('smtplib.SMTP')
    def test_send_message(self, SMTP):
        mbx = notification.SMTPMailbox('a@example.com')
        mbx.notify('foo')
        assert SMTP().sendmail.called
