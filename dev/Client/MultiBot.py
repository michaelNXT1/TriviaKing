import concurrent.futures
import sys

from dev.Client import Bot


def main():
    num_bots = check_args()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=num_bots)
    for i in range(num_bots):
        pool.submit(Bot.main)
    pool.shutdown(wait=True)


def check_args():
    if len(sys.argv) != 2:
        print("Error: Please provide only one argument to the program. Exiting..")
        sys.exit(1)
    try:
        num_bots = int(sys.argv[1])
        if num_bots <= 0:
            raise ValueError("The number must be greater than 0")
        return num_bots
    except ValueError as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
