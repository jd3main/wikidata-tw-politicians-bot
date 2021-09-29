import tw_politicians_bot
import argparse
from distutils.util import strtobool

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', type=str, default=True, help='False to turn off test mode, default: True')
    parser.add_argument('-n', type=int, default=-1, help='Import first n candidates only')
    parser.add_argument('-s', '--sleep', type=float, default=1, help='Sleep time in seconds for each write operation')
    args = parser.parse_args()

    args.test = bool(strtobool(str(args.test)))
    tw_politicians_bot.main(is_test=args.test, head=args.n, sleep_time=args.sleep)
