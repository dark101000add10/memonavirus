import os, re
import numpy
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

past_infection_files = ["../../data/" + f for f in os.listdir("../../data") if f.startswith("memes_infections") and f.endswith(".log")]


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)
past_infection_files = natural_sort(past_infection_files)

xvals = []
yvals = []
for pif in past_infection_files:
    xvals.append("2020-03-{} : {}:00".format(pif.split('.')[-3], pif.split('.')[-2]))
    total = 0
    with open(pif, "r") as fp:
        for line in fp.readlines():
            total += 1
    yvals.append(total)

z1 = numpy.polyfit([i for i in range(0, len(xvals))], yvals, 1)
z2 = numpy.polyfit([i for i in range(0, len(xvals))], yvals, 8)
p1 = numpy.poly1d(z1)
p2 = numpy.poly1d(z2)

legend = [Line2D([0], [0], marker='o', color='w', label='{} Total Infections'.format(sum(yvals)), markerfacecolor='r', markersize=15)]

fig, axs = plt.subplots()
axs.bar(xvals, yvals, color=(1, 0, 0, 1))
axs.plot([i for i in range(0, len(xvals))], p1([i for i in range(0, len(xvals))]), "b--")
axs.plot([i for i in range(0, len(xvals))], p2([i for i in range(0, len(xvals))]), "g--")
axs.legend(handles=legend)
plt.xticks(rotation=45)
fig.suptitle('r/memes Memonavirus Outbreak by hour')
plt.show()
