import argparse
import asyncio
import uvicorn

from .config import settings
from .pipeline import refresh_event


def main():
    parser = argparse.ArgumentParser(prog='parlay')
    sub = parser.add_subparsers(dest='cmd', required=True)

    once = sub.add_parser('once')
    once.add_argument('--event', required=False, help='Event URL')

    watch = sub.add_parser('watch')
    watch.add_argument('--event', required=False, help='Event URL')
    watch.add_argument('--host', default='127.0.0.1')
    watch.add_argument('--port', type=int, default=8000)

    args = parser.parse_args()

    if args.cmd == 'once':
        if args.event:
            settings.EVENT_URL = args.event
        asyncio.run(refresh_event())
    elif args.cmd == 'watch':
        if args.event:
            settings.EVENT_URL = args.event
        uvicorn.run('app.server:app', host=args.host, port=args.port, reload=False)


if __name__ == '__main__':
    main()
