import sqlite3
import os
#
# TODO could be that this might change to a primary index later using uuid
#
class FileCache:
    def __init__(self, name):
        print ("Initializing: " + name)
        self.con = sqlite3.connect(name)
        self.cur = self.con.cursor()
        self.name = name
        self.time = int(os.stat(name).st_mtime)
        print (self.time)

    def createCache(self, latest, subdir=None):
        """
        creates filecache and userinformation if non existent
        deletes complete filecache entries in case a file is newer
        or filecache entries when subdir is mentioned
        """
        res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='userinformation'")
        if res.fetchone() is None:
            print ("Need to create user table")
            self.cur.execute("CREATE TABLE userinformation(uuid, tags)")

        res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='filecache'")
        if res.fetchone() is None:
            print ("Need to create table")
            self.cur.execute("CREATE TABLE filecache(name, uuid, path, folder, obj_file, thumbfile, author, tags)")
            return(True)

        if subdir is None:
            if latest > self.time:
                print ("Need to cleanup file table")
                self.cur.execute("DELETE FROM filecache")
                return (True)
            else:
                return(False)
        else:
            print("DELETE FROM filecache where folder = " +  subdir)
            self.cur.execute("DELETE FROM filecache where folder = ?", (subdir,))
            self.con.commit()
            return (True)

    def getEditParamInfo(self, uuid):
        return(self.cur.execute("SELECT tags FROM filecache where uuid = ?", (uuid,)))

    def getEditParamUser(self, uuid):
        return(self.cur.execute("SELECT tags FROM userinformation where uuid = ?", (uuid,)))

    def deleteParamUser(self, uuid):
        self.cur.execute("delete FROM userinformation where uuid = ?", (uuid,))
        self.con.commit()

    def insertParamUser(self, uuid, tags):
        self.deleteParamUser(uuid)
        self.cur.execute("insert into userinformation values(?, ?)", (uuid, tags))
        self.con.commit()

    def updateParamInfo(self, uuid, thumbfile):
        self.cur.execute("update filecache set thumbfile = ?  where uuid = ?", (thumbfile, uuid))
        self.con.commit()

    def listCache(self):
        return(self.cur.execute("SELECT * FROM filecache ORDER BY name COLLATE NOCASE ASC"))

    def listUserInfo(self):
        return(self.cur.execute("SELECT * FROM userinformation"))

    def listCacheMatch(self):
        corrected = self.listUserInfo()
        match = {}
        for row in corrected:
            match[row[0]] = row[1]
        rows = self.listCache()
        return (rows, match)

    def insertCache(self, data):
        self.cur.executemany("insert into filecache values(?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.con.commit()
        self.time = int(os.stat(self.name).st_mtime)

    def __del__(self):
        self.cur.close()

