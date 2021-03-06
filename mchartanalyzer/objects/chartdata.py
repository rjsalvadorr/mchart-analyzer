from .basedata import BaseDataObject

class ChartData(BaseDataObject):
    """
    Encapsulates data extracted from a chord chart.
    """

    def __init__(self, databaseRow=None):
        BaseDataObject.__init__(self)

        self.songId = 0
        self.source = ""
        self.chordsSpecific = []
        self.sections = []
        self.isNew = 0

        # properties not used in the database
        self.artist = None
        self.title = None

        if databaseRow:
            self.id = databaseRow[0]
            self.songId = databaseRow[1]
            self.source = databaseRow[2]
            self.chordsSpecific = self._convertStringToList(databaseRow[3])
            self.sections = self._convertStringToList(databaseRow[4])
            self.isNew = databaseRow[5]
            self.updateTime = databaseRow[6]


    def setChordListFromString(self, chordListStr):
        convertedList = self._convertStringToList(chordListStr)
        self.chordsSpecific = convertedList


    def setSectionsFromString(self, sectionsStr):
        convertedList = self._convertStringToList(sectionsStr)
        self.sections = convertedList


    def getChordListString(self):
        return self._convertListToString(self.chordsSpecific)


    def getSectionListString(self):
        return self._convertListToString(self.sections)


    def toLogString(self):
        stringRep = "SONG: " + self.title.upper() + "\n"
        stringRep += "ARTIST: " + self.artist + "\n"
        stringRep += "SOURCE: " + self.source + "\n"

        if self.chordsSpecific:
            stringRep += "CHORDS:\n"
            stringRep += self.getChordListString() + "\n"

        if self.sections:
            stringRep += "SECTIONS:\n"
            stringRep += self.getSectionListString() + "\n"

        return stringRep


    def __str__(self):
        stringRep = "ChartData { id=" + str(self.id) + ", "

        stringRep += "songId=" + str(self.songId) + ", "
        stringRep += "source=" + self.source + ", "
        stringRep += "chordsSpecific=[" + self.getChordListString() + "], "
        stringRep += "sections=[" + self.getSectionListString() + "], "
        stringRep += "isNew=" + str(self.isNew) + ", "

        stringRep += "updateTime=" + self.updateTime + " }"

        return stringRep
