from dotenv import load_dotenv
from bot.bot import start_bot


def main():
    load_dotenv()
    start_bot()


if __name__ == "__main__":
    main()
