import types
from unittest import mock

from jaraco.email import messages

SAMPLE = (
    'Received: from mail.example.com ([192.0.2.5]) by mx.example.org\n'
    'Subject: hello\n'
    '\n'
    'body\n'
)


def imap_item(id, msg):
    return 'OK', ((f'{id} (BODY[HEADER])', msg), ')')


def test_parse_imap_message():
    msg = messages.MessageHandler.parse_imap_message(imap_item(1, SAMPLE))
    assert msg.sender == '192.0.2.5'
    assert msg.domain == 'example.com'
    assert msg.subnet == '192.0.2.0/24'


def test_get_login_params(monkeypatch):
    monkeypatch.setattr(messages, 'getuser', lambda: 'alice')
    monkeypatch.setattr('builtins.input', lambda prompt: '')
    monkeypatch.setattr(messages.keyring, 'get_password', lambda *args: 'secret')
    options = types.SimpleNamespace(
        username=None, hostname='imap.example.com', save_password=False
    )
    messages.get_login_params(options)
    assert options.username == 'alice'
    assert options.password == 'secret'


@mock.patch.object(messages, 'IMAP4_SSL')
def test_get_folder_messages(IMAP4_SSL):
    server = IMAP4_SSL.return_value
    server.search.return_value = 'OK', [b'1']
    server.fetch.return_value = imap_item(1, SAMPLE)
    options = types.SimpleNamespace(
        username='alice', password='secret', hostname='imap.example.com'
    )
    handler = messages.MessageHandler(options)
    (msg,) = handler.get_folder_messages('INBOX')
    assert msg.sender == '192.0.2.5'
    server.login.assert_called_with('alice', 'secret')
