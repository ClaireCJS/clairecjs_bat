# clairecjs_utils

clairecjs_utils is a set of utility functions written by Claire CJS 

# What are some functions?

After doing a ``import clairecjs_utils as claire``, can do some things such as:

* safe file renaming:
  filename_we_actually_renamed_it_to = rename(before_rename_filename, after_rename_filename)

* easy GPT querying:
  answer = ask_GPT("How much would could a woodchuck chuck?")

* claire.tick() - run this inside loops to color-cycle your screen colors (set mode="bg" to do background instead of foreground, or mode="both" for both) so you can tell your process is still doing stuff, with out cluttering up your screen output. Run claire.tock() when done to attempt to reset colors to normal. I said attempt. This is a work in progress.

The functions themselves should be documented for more granular usage info, but these are the basic calls.

# Installation: Python

Just install the appropriate packages, and the script should be ready to go.

```bash
pip install clairecjs_utils
```

Just kidding! I don't have my package published. You just gotta get the files imported manually.  
Clone this into lib\site-packages-clairecjs_util 

# Tests

A few unit tests, but really could use more, if anyone wants to write some.


# Contributing: Modification

Feel free to make your own version with neato changes, if you are so inspired.

# Those wacky BAT files?

I use TCC -- Take Command Command Line.
Technically, my .BAT files are .BTM files.

# License

[The Unlicense](https://choosealicense.com/licenses/unlicense/)

