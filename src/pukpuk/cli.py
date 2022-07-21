import sys

from pukpuk import (
    base,
    logs,
)


def main():
    app = base.Application()
    try:
        app.parse(sys.argv[1:])
    except Exception as exc:
        logs.logger.error(exc)
    except KeyboardInterrupt:
        logs.logger.info(f'Exiting')


if __name__ == '__main__':
    sys.exit(main())
