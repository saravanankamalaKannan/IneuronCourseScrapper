import pymongo

class MongoDatabaseHandler:
    def __init__(self, username, pwd, database, collection):
        self.__username = username
        self.__pwd = pwd
        self.__databaseName = database
        self.__collectionName = collection
        self.__connectionStr = "mongodb+srv://{username}:{pwd}@cluster0.ljxxh.mongodb.net/myFirstDatabase?retryWrites=true&w=majority".format(username=username, pwd=pwd)

    def __del__(self):
        self.Disconnect()

    def ConnectAndCreateDB(self):
        self.__client = pymongo.MongoClient(self.__connectionStr)
        self.__db = self.__client[self.__databaseName]
        self.__collection = self.__db[self.__collectionName]

    def GetDatabaseNames(self):
        return self.__client.list_database_names()

    def InsertOneData(self, dataToInsert):
        self.__collection.insert_one(dataToInsert)

    def Disconnect(self):
        self.__client.close()



