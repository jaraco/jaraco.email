import asyncio
import argparse

from aiosmtpd.controller import Controller


def _get_args():
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help="Bind to port", default=25)
    return p.parse_args()


class DebuggingHandler:
    async def handle_DATA(self, server, session, envelope):
        print('peer:', session.peer)
        print('mailfrom:', envelope.mail_from)
        print('rcpttos:', envelope.rcpt_tos)
        return '250 OK'


def start_simple_server():
    "A simple mail server that sends a simple response"
    args = _get_args()
    controller = Controller(DebuggingHandler(), hostname='', port=args.port)
    controller.start()
    asyncio.new_event_loop().run_forever()
