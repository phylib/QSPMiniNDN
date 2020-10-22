import argparse
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-changes', dest='numChanges', type=int, required=True)
    parser.add_argument('--time-between', dest='timeBetween', type=int, default=5, help="Time in seconds between changes are applied", required=True)
    parser.add_argument('--evaluation-time', dest='evalTime', type=int, default=300)

    args = parser.parse_args()
    numChanges = args.numChanges
    timeBetween = args.timeBetween * 20
    evalTime = args.evalTime * 20

    currentTime = 10

    random.seed(0)
    changes = set()
    while len(changes) < numChanges:
        x = random.randint(0, 2**15 - 1)
        y = random.randint(0, 2**15 - 1)
        xy = "{},{}".format(x,y)
        changes.add(xy)

    print("tick\tchunks")
    print("0\t0,0;65535,65535")
    while currentTime < evalTime:
        if currentTime%timeBetween == 0:
            print("{}\t{}".format(currentTime, ";".join(list(changes))))
        else:
            print("{}\t".format(currentTime))
        currentTime += 10
