while (<>) {
    s/\e\[[\d;]*[mK]//g;
    print;
}