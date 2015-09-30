import random, sys

class Goody(object):
    generateT   = None
    types       = [ {"name": "Rum",     "category": "A"}, 
                    {"name": "Vodka",   "category": "A"},
                    {"name": "Gin",     "category": "A"},
                    {"name": "Cola",    "category": "N"},
                    {"name": "Wasser",  "category": "N"},
                    {"name": "Orange",  "category": "N"},
                    {"name": "Mango",   "category": "N"}]

    def getNextGoodyType(self, collectedGoodies):
        #return random.randint(0, len(Goody.types) - 1)


        weights = [10000] * len(Goody.types)
        # for i, wGoody in enumerate(Goody.types):
        #     if wGoody['category'] == "A":
        #         weights[i] = 4096
        #     else:
        #         weights[i] = 8192


        for goody in collectedGoodies:
            cat = Goody.types[goody]['category']
            for i, wGoody in enumerate(Goody.types):
                if cat == "A":
                    if wGoody['category'] == "A" and i != goody:
                        weights[i] /= 5
                    if i == goody:
                        weights[i] /= 2
                elif cat == "N":
                    if wGoody['category'] == "N" and i != goody:
                        weights[i] /= 4
                    if i == goody:
                        weights[i] /= 1.5

        if Goody.generateT:
            if Goody.generateT == "N":
                for i, wGoody in enumerate(Goody.types):
                    if wGoody['category'] != "N":
                        weights[i] = 0
            if Goody.generateT == "A":
                for i, wGoody in enumerate(Goody.types):
                    if wGoody['category'] != "A":
                        weights[i] = 0


        t = random.randint(0, int(sum(weights)))

        s = 0
        for i in range(len(weights)):
            s = s + weights[i]
            if t <= s:
                return i

inCup = []
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        inCup.append(int(sys.argv[i]))

g = Goody()


for i in inCup:
    print "Already in cup: " + Goody.types[i]["name"]


a = [0] * len(Goody.types)
for i in range(10000):
    i = g.getNextGoodyType(inCup)
    a[i] += 1

for i, count in enumerate(a):
    print str(i) + ". " + Goody.types[i]["name"] + " - " + str(round(float(count)/sum(a)*100)) + " %"




