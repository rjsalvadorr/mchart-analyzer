import os
import sqlite3
import traceback
from datetime import datetime

from . import constants
from .objects.artistdata import ArtistData
from .objects.songdata import SongData
from .objects.chartdata import ChartData
from .objects.artistcalculations import ArtistCalculations
from .objects.chartcalculations import ChartCalculations

class DatabaseHandler:
    """
    Class responsible for handling database operations.
    """

    def __init__(self, testMode=None):
        self.dbConnection = None
        self.dbOpened = False

    def _connect(self):
        if not self.dbOpened:
            # This also creates a database if it doesn't exist!
            self.dbConnection = sqlite3.connect(constants.DATABASE_FILE_PATH)
            self.dbOpened = True
        return self.dbConnection.cursor()

    def _commit(self):
        self.dbConnection.commit()

    def _close(self):
        if self.dbOpened:
            self.dbConnection.close()
            self.dbOpened = False

    def _commitAndClose(self):
        if self.dbOpened:
            self.dbConnection.commit()
            self.dbConnection.close()
            self.dbOpened = False


    def saveArtistData(self, artistData):
        """
        Saves artist data to the database.
        """
        insertStmt = "INSERT INTO ARTISTS('name','source_names','source_urls','update_time') VALUES (\'{artistName}\', \'{sourceNames}\', \'{sourceUrls}\', \'{updateTime}\')"
        updateStmt = "UPDATE ARTISTS SET 'source_names' = \'{sourceNames}\', 'source_urls' = \'{sourceUrls}\', 'update_time' = \'{updateTime}\' WHERE name=\'{artistName}\'"

        try:
            c = self._connect()
            existingArtist = self.getArtistByName(artistData.name, keepConnectionOpen=True)
            timestampStr = datetime.now().strftime(constants.DATETIME_FORMAT)

            if existingArtist:
                # Artist with this name already exists. Update it.
                finalQuery = updateStmt.format(artistName=artistData.name, sourceNames=artistData.getSourceNamesAsString(), sourceUrls=artistData.getSourceUrlsAsString(), updateTime=timestampStr)
                # print("Running query: " + finalQuery)
                c.execute(finalQuery)
            else:
                # Artist does not exist yet. Insert new record.
                finalQuery = insertStmt.format(artistName=artistData.name, sourceNames=artistData.getSourceNamesAsString(), sourceUrls=artistData.getSourceUrlsAsString(), updateTime=timestampStr)
                # print("Running query: " + finalQuery)
                c.execute(finalQuery)

        except sqlite3.IntegrityError as exc:
            print(repr(exc))

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()


    def saveSongData(self, artistData, songData):
        """
        Saves song data to the database.
        If a song with the same name exists in the database, nothing happens.
        """
        insertStmt = "INSERT INTO SONGS('artist_id','title','update_time') VALUES ({artistId}, \'{songTitle}\', \'{updateTime}\')"

        try:
            c = self._connect()
            existingArtist = self.getArtistByName(artistData.name, keepConnectionOpen=True)
            existingSong = self.getSongByTitle(songData.title, keepConnectionOpen=True)
            timestampStr = datetime.now().strftime(constants.DATETIME_FORMAT)

            if not existingSong:
                # Song does not exist yet. Insert new record.
                finalQuery = insertStmt.format(artistId=existingArtist.id, songTitle=songData.title, updateTime=timestampStr)
                # print("Running query: " + finalQuery)
                c.execute(finalQuery)

        except sqlite3.IntegrityError as exc:
            print(repr(exc))

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()


    def saveChartData(self, songData, chartData):
        """
        Saves chart data to the database.
        If a chart with the same URL exists, the existing record is updated with the newer chords and sections.
        """
        insertStmt = "INSERT INTO CHARTS('song_id','source_url','chords_specific','sections','is_new','is_definitive','update_time') VALUES ({songId}, \'{url}\', \'{chordList}\', \'{sectionList}\', 1, \'{isDefinitive}\', \'{updateTime}\')"

        updateStmt = "UPDATE CHARTS SET 'chords_specific' = \'{chordList}\', 'sections' = \'{sectionList}\', 'is_new' = 1, 'update_time' = \'{updateTime}\' WHERE song_id={songId} AND source_url=\'{url}\'"

        try:
            c = self._connect()
            existingChart = self.getChartByUrl(chartData.source, keepConnectionOpen=True)
            existingSong = self.getSongByTitle(songData.title, keepConnectionOpen=True)
            timestampStr = datetime.now().strftime(constants.DATETIME_FORMAT)

            if existingChart:
                # Chart from this source already exists. Update it.
                c.execute(updateStmt.format(songId=existingSong.id, url=chartData.source, chordList=chartData.getChordListString(), sectionList=chartData.getSectionListString(), isDefinitive=chartData.isDefinitive, updateTime=timestampStr))
            else:
                # Chart does not exist yet. Insert new record.
                c.execute(insertStmt.format(songId=existingSong.id, url=chartData.source, chordList=chartData.getChordListString(), sectionList=chartData.getSectionListString(), isDefinitive=chartData.isDefinitive, updateTime=timestampStr))

        except sqlite3.IntegrityError as exc:
            print(repr(exc))

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()


    def saveChartCalculationData(self, chartData, chartCalcs):
        """
        Saves chart calculations to the database.
        """
        insertCalcsStmt = "INSERT INTO CHART_CALCS('chart_id', 'key', 'key_certainty', 'chords_general', 'num_chords', 'update_time') VALUES ({chartId}, \'{key}\', \'{keyCertainty}\', \'{chordsGeneral}\', \'{numChords}\', \'{updateTime}\')"

        updateCalcsStmt = "UPDATE CHART_CALCS SET 'key' = \'{key}\', 'key_certainty' = \'{keyCertainty}\', 'chords_general' = \'{chordsGeneral}\', 'num_chords' = \'{numChords}\', 'update_time' = \'{updateTime}\' WHERE chart_id={chartId}"

        updateChartStmt = "UPDATE CHARTS SET is_new = 0, update_time = \'{updateTime}\' WHERE id={chartId}"

        selectCalcsStmt = "SELECT * from CHART_CALCS WHERE chart_id = {chartId}"

        try:
            c = self._connect()
            c.execute(selectCalcsStmt.format(chartId=chartData.id))
            existingChartCalc = c.fetchone()
            timestampStr = datetime.now().strftime(constants.DATETIME_FORMAT)

            if existingChartCalc:
                # Chart from this source already exists. Update it.
                c.execute(updateCalcsStmt.format(chartId=chartData.id, key=chartCalcs.key, keyCertainty=chartCalcs.keyAnalysisCertainty, chordsGeneral=chartCalcs.getChordListString(), numChords=chartCalcs.numChords, updateTime=timestampStr))
            else:
                # Chart does not exist yet. Insert new record.
                c.execute(insertCalcsStmt.format(chartId=chartData.id, key=chartCalcs.key, keyCertainty=chartCalcs.keyAnalysisCertainty, chordsGeneral=chartCalcs.getChordListString(), numChords=chartCalcs.numChords, updateTime=timestampStr))

            # Update the chart, toggle "is_new" to 0
            c.execute(updateChartStmt.format(chartId=chartData.id,  updateTime=timestampStr))


        except sqlite3.IntegrityError as exc:
            print(repr(exc))

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()


    def saveArtistCalculationData(self, chartData):
        """
        Saves artist calculations to the database.
        """
        try:
            c = self._connect()
            # ...

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()


    def getArtistByName(self, artistName, keepConnectionOpen=None):
        """
        Retrieves an artist with the given name.
        Returns "None" if a record isn't found.
        """
        try:
            c = self._connect()
            c.execute("SELECT * FROM ARTISTS WHERE name = ?", (artistName,))
            row = c.fetchone()

            if row:
                newArtistData = ArtistData()

                newArtistData.id = row[0]
                newArtistData.name = row[1]
                newArtistData.setSourceNamesFromString(row[2])
                newArtistData.setSourceUrlsFromString(row[3])
                newArtistData.updateTime = row[4]

                return newArtistData
            else:
                return None

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            if not keepConnectionOpen:
                self._close()

        # If it gets to this point, I don't even know what to do.
        return None

    # TODO - fix this method, so it's getting a song by title AND artist name!!!
    # Remember, multiple musicians can release songs with the same title!!
    def getSongByTitle(self, title, keepConnectionOpen=None):
        """
        Retrieves a song with the given title.
        Returns "None" if a record isn't found.
        """
        try:
            c = self._connect()
            c.execute("SELECT * FROM SONGS WHERE title = ?", (title,))
            row = c.fetchone()

            if row:
                newSongData = SongData()

                newSongData.id = row[0]
                newSongData.artistId = row[1]
                newSongData.title = row[2]
                newSongData.updateTime = row[3]

                return newSongData
            else:
                return None

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            if not keepConnectionOpen:
                self._close()

        return 0


    def getSongById(self, songId, keepConnectionOpen=None):
        """
        Retrieves a song with the given title.
        Returns "None" if a record isn't found.
        """
        try:
            c = self._connect()
            c.execute("SELECT * FROM SONGS WHERE id = ?", (songId,))
            row = c.fetchone()

            if row:
                newSongData = SongData()

                newSongData.id = row[0]
                newSongData.artistId = row[1]
                newSongData.title = row[2]
                newSongData.updateTime = row[3]

                return newSongData
            else:
                return None

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            if not keepConnectionOpen:
                self._close()

        return 0


    def getChartsForSong(self, songData):
        """
        Retrieves all charts for a given song.
        """
        chartRecords = []
        try:
            c = self._connect()

            c.execute("SELECT CHARTS.* FROM SONGS INNER JOIN CHARTS ON SONGS.id = CHARTS.song_id WHERE CHARTS.song_id = ?", (songData.id,))

            for row in c:
                newChartData = ChartData()

                newChartData.id = row[0]
                newChartData.songId = row[1]
                newChartData.source = row[2]
                newChartData.setChordListFromString(row[3])
                newChartData.setSectionsFromString(row[4])
                newChartData.isNew = row[5]
                newChartData.isDefinitive = row[6]
                newChartData.updateTime = row[7]

                chartRecords.append(newChartData)

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._close()

        return chartRecords


    def getChartByUrl(self, sourceUrl, keepConnectionOpen=None):
        """
        Retrieves a chart with the given source URL.
        Returns "None" if a record isn't found.
        """
        try:
            c = self._connect()
            c.execute("SELECT * FROM CHARTS WHERE source_url = ?", (sourceUrl,))
            row = c.fetchone()

            if row:
                newChartData = ChartData()

                newChartData.id = row[0]
                newChartData.songId = row[1]
                newChartData.source = row[2]
                newChartData.setChordListFromString(row[3])
                newChartData.setSectionsFromString(row[4])
                newChartData.isNew = row[5]
                newChartData.isDefinitive = row[6]
                newChartData.updateTime = row[7]

                return newChartData
            else:
                return None

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            if not keepConnectionOpen:
                self._close()

        return None


    def getArtistsWithFreshCharts(self):
        """
        Retrieves artists with charts that haven't been analyzed yet.
        Returns an empty list if there are no such artists
        """
        artistRecords = []
        try:
            c = self._connect()
            c.execute("SELECT ARTISTS.* FROM ARTISTS INNER JOIN SONGS ON ARTISTS.id = SONGS.artist_id INNER JOIN CHARTS ON SONGS.id = CHARTS.song_id WHERE CHARTS.is_new != 0 GROUP BY ARTISTS.name")
            for row in c:
                newArtistData = ArtistData()

                newArtistData.id = row[0]
                newArtistData.name = row[1]
                newArtistData.setSourceNamesFromString(row[2])
                newArtistData.setSourceUrlsFromString(row[3])
                newArtistData.updateTime = row[4]

                artistRecords.append(newArtistData)

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._close()

        return artistRecords


    def getAllArtists(self):
        """
        Retrieves artists.
        Returns an empty list if there are no such artists
        """
        artistRecords = []
        try:
            c = self._connect()

            c.execute("SELECT * FROM ARTISTS")
            for row in c:
                newArtistData = ArtistData()

                newArtistData.id = row[0]
                newArtistData.name = row[1]
                newArtistData.setSourceNamesFromString(row[2])
                newArtistData.setSourceUrlsFromString(row[3])
                newArtistData.updateTime = row[4]

                artistRecords.append(newArtistData)

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._close()

        return artistRecords


    def getFreshChartsForArtist(self, artistName):
        """
        For a given artist, retrieves charts that haven't been analyzed yet.
        Returns an empty list if there are no new charts.
        """
        chartRecords = []
        try:
            c = self._connect()

            c.execute("SELECT CHARTS.* FROM ARTISTS INNER JOIN SONGS ON ARTISTS.id = SONGS.artist_id INNER JOIN CHARTS ON SONGS.id = CHARTS.song_id WHERE CHARTS.is_new != 0 AND ARTISTS.name = ?", (artistName.upper(),))

            for row in c:
                newChartData = ChartData()

                newChartData.id = row[0]
                newChartData.songId = row[1]
                newChartData.source = row[2]
                newChartData.setChordListFromString(row[3])
                newChartData.setSectionsFromString(row[4])
                newChartData.isNew = row[5]
                newChartData.isDefinitive = row[6]
                newChartData.updateTime = row[7]

                chartRecords.append(newChartData)

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._close()

        return chartRecords


    def getAllChartsForArtist(self, artistName):
        """
        For a given artist, retrieves charts that haven't been analyzed yet.
        Returns an empty list if there are no new charts.
        """
        chartRecords = []
        try:
            c = self._connect()

            c.execute("SELECT CHARTS.* FROM ARTISTS INNER JOIN SONGS ON ARTISTS.id = SONGS.artist_id INNER JOIN CHARTS ON SONGS.id = CHARTS.song_id WHERE ARTISTS.name = ?", (artistName.upper(),))

            for row in c:
                newChartData = ChartData()

                newChartData.id = row[0]
                newChartData.songId = row[1]
                newChartData.source = row[2]
                newChartData.setChordListFromString(row[3])
                newChartData.setSectionsFromString(row[4])
                newChartData.isNew = row[5]
                newChartData.isDefinitive = row[6]
                newChartData.updateTime = row[7]

                chartRecords.append(newChartData)

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._close()

        return chartRecords


    def getBasicArtistStatistics(self, artistData):
        """
        For a given artist, retrieves basic statistics.
        """
        artistCalcs = ArtistCalculations()

        stmtArtistSongs = "SELECT SONGS.*, CHART_CALCS.key FROM SONGS INNER JOIN CHARTS ON SONGS.id = CHARTS.song_id INNER JOIN CHART_CALCS ON CHARTS.id = CHART_CALCS.chart_id WHERE artist_id = ? GROUP BY SONGS.id"

        stmtArtistCharts = "SELECT CHARTS.*, CHART_CALCS.num_chords FROM SONGS INNER JOIN CHARTS ON SONGS.id = CHARTS.song_id INNER JOIN CHART_CALCS ON CHARTS.id = CHART_CALCS.chart_id WHERE artist_id = ?"

        try:
            c = self._connect()

            c.execute(stmtArtistSongs, (artistData.id,))
            for row in c:
                artistCalcs.numSongs += 1
                keyString = row[4]
                if keyString.lower().find("major") >= 0:
                    artistCalcs.numMajorKeys += 1

            c.execute(stmtArtistCharts, (artistData.id,))
            for row in c:
                artistCalcs.numCharts += 1
                artistCalcs.numChords += row[8]


        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._close()

        artistCalcs.numMinorKeys = artistCalcs.numCharts - artistCalcs.numMajorKeys


        return artistCalcs


    def initializeDatabase(self):
        """
        Initializes database.
        Creates database file if it doesn't exist.
        If a database already exists, this function will delete it and recreate it!
        """

        try:
            # delete database if it exists.
            os.remove(constants.DATABASE_FILE_PATH)
            print("Database file deleted!")
        except OSError as exc:
            print(repr(exc))

        try:

            c = self._connect()

            print("Initializing Database!")

            c.execute("CREATE TABLE ARTISTS ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT UNIQUE, `source_names` TEXT, `source_urls` TEXT, `update_time` TEXT )")
            c.execute("CREATE TABLE `SONGS` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `artist_id` INTEGER, `title` TEXT, `update_time` TEXT, FOREIGN KEY(`artist_id`) REFERENCES ARTISTS(id) )")
            c.execute("CREATE TABLE CHARTS ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `song_id` INTEGER, `source_url` TEXT UNIQUE, `chords_specific` TEXT, `sections` TEXT, `is_new` INTEGER, `is_definitive` INTEGER, `update_time` TEXT, FOREIGN KEY(`song_id`) REFERENCES `SONGS`(`id`) )")

            c.execute("CREATE TABLE \"ARTIST_CALCS\" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `artist_id` INTEGER UNIQUE, `num_chords` INTEGER, `common_chords_spec` TEXT, `common_chords_gen` TEXT, `update_time` TEXT, FOREIGN KEY(`artist_id`) REFERENCES `ARTISTS`(`id`) )")
            c.execute("CREATE TABLE \"CHART_CALCS\" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `chart_id` INTEGER UNIQUE, `key` TEXT, `key_certainty` TEXT, `chords_general` TEXT, `num_chords` INTEGER, `update_time` TEXT, FOREIGN KEY(`chart_id`) REFERENCES `CHARTS`(`id`) )")

            c.execute("CREATE TABLE `ARTISTS_DUPL_ASC` ( `id` INTEGER, `primary_artist_id` INTEGER, `duplicate_artist_id` INTEGER, PRIMARY KEY(`id`) )")
            c.execute("CREATE TABLE `SONGS_DUPL_ASC` ( `id` INTEGER, `primary_song_id` INTEGER, `duplicate_song_id` INTEGER, PRIMARY KEY(`id`) )")

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()


    def purgeDatabase(self):
        """
        Removes all data from the database.
        """
        try:
            c = self._connect()

            print("PURGING ALL DATA FROM THE DATABASE!")
            c.execute("DELETE FROM ARTISTS")
            c.execute("DELETE FROM ARTIST_CALCS")
            c.execute("DELETE FROM CHARTS")
            c.execute("DELETE FROM CHART_CALCS")
            c.execute("DELETE FROM SONGS")

        except Exception as exc:
            print("UNEXPECTED ERROR: " + repr(exc))
            print(traceback.format_exc())

        finally:
            self._commitAndClose()
