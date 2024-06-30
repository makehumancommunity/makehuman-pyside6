
class tagLogic():
    def __init__(self, json):
        self.reserved = ["Translate", "GuessName", "Shortcut"]
        self.tagreplace = {}
        self.tagfromname = {}
        self.tagproposals = []
        self.json = json

    def proposals(self):
        return(self.tagproposals)

    def convertJSON(self, json, separator=":", prepend = ""):
        for elem in json:
            if elem in self.reserved:
                continue
            j = json[elem]
            if type(j) is dict:
                self.convertJSON(j, separator, prepend + elem + separator)
            elif type(j) is list:
                for l in j:
                    self.tagproposals.append((prepend + elem + separator + l).lower())

    def createTagGroups(self, subtree, path):
        """
        create texts to prepend certain tags, can also translate tags
        """
        for elem in subtree:
            if isinstance(elem, str):
                if elem == "Translate":                             # extra, change by word
                    for l in subtree[elem]:
                        self.tagreplace[l.lower()] = subtree[elem][l]
                    continue
                if elem == "GuessName":                             # extra, change by word
                    for l in subtree[elem]:
                        self.tagfromname[l.lower()] = subtree[elem][l]
                    continue
                if isinstance(subtree[elem], dict):
                    self.createTagGroups(subtree[elem], path + ":" + elem.lower())
                elif isinstance(subtree[elem], list):
                    if elem == "Shortcut":
                        pass
                    else:
                        for l in subtree[elem]:
                            repl = path + ":" + elem.lower()
                            self.tagreplace[l.lower()] = repl[1:]       # get rid of first ":"

    def completeTags(self, name, tags):
        """
        replace tags by tags with prepended strings or check name
        """
        newtags = []
        for tag in tags:
            ltag = tag.lower()
            if ltag in self.tagreplace:
                elem = self.tagreplace[ltag]
                if elem is not None:
                    if elem.startswith("="):        # complete replacement
                        ntag = elem[1:]
                    else:
                        ntag = elem+":"+ltag
                    if ntag not in newtags:
                        newtags.append(ntag)
            else:
                if tag not in newtags:
                    newtags.append(tag)

        for tag in self.tagfromname:
            if tag in name:
                ntag = self.tagfromname[tag]
                if ntag not in newtags:
                    newtags.append(ntag)
        return (newtags)

    def create(self):
        self.convertJSON(self.json)
        self.createTagGroups(self.json, "")

