#!/usr/bin/python3
node = "s{0}: _ network=/world router=/s{0}.Router/ site=/s{0}"
link = "s{0}:central delay=10ms"

def printTopo(size):
    print("[nodes]")
    for i in range(0, size):
        print(node.format(i))
    print("[links]")
    for i in range(0, size):
        print(link.format(i))

printTopo(64)