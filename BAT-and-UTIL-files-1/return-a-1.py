from colorama import init, Fore
init()


def main():
    message = f"{Fore.RED}1 from main is failure and should produce an errorlevel of 1, though we *MAY* have to throw an exception for this"
    print(message)
    raise Exception(message)
    return 1

if __name__ == "__main__":
    main()
