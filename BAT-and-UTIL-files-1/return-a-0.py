from colorama import init, Fore
init()


def main():
    print(f"{Fore.GREEN}0 from main is success and should have an errorlevel of 0. No exception is being thrown.")
    return 0

if __name__ == "__main__":
    main()
