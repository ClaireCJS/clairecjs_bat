import sys,json,__main__
marker=42
assert __main__.marker==42
print(json.dumps([__file__,sys.argv[1:]]))
