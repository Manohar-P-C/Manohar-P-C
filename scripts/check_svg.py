import re, sys
svg = open(sys.argv[1]).read()
ys = [float(m) for m in re.findall(r'y="([\d.]+)"', svg)]
print("Min y:", min(ys), "Max y:", max(ys))
