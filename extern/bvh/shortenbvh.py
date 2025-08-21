#!/usr/bin/python3

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Shorten BVH File")
    parser.add_argument("filename", type=str, help="filename")
    parser.add_argument("-V", type=float, default=0.0, help="move character vertical in V units")
    parser.add_argument("-C", action="store_true", help="move character vertical to 0.0")

    args = parser.parse_args()

    cols = 0
    f = open(args.filename, "r")
    corrected = False
    corrvalue = 0.0
    h = None
    if args.C:
        h = 0.0
    elif args.V != 0.0:
        h = args.V

    for line in f:
        new = line.replace('\t', " ") # readability, but wrong for BVH
        pos = line.find("CHANNELS")
        if pos > -1:
            s = line[pos+9:]
            words = s.split()
            try:
                num = int(words[0])
                cols += num
            except:
                pass
            print(new, end='')
            continue

        words = line.split()
        try:
            float(words[0])
            text = ""
            for i, word in enumerate(words):
                val = float(word)
                if i == 2:
                    if h is not None:
                        if corrected is False:
                            corrvalue = val - h
                            val = h
                            corrected = True
                        else:
                            val-= corrvalue

                if val < 0.0001 and val > -0.0001:
                    text += " 0"
                else:
                    text += " " + str(round(val,4))
            print (text[1:])
        except ValueError:
            print(new, end='')
