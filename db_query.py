


class ClientHandler():

    def __init__(self,
                 mongo_url=None):


        self._mongo_url = mongo_url


        self._detected_codes = []


    def setup_mongo(self):
        if self._mongo_url != None:
            self._mongo_url = mongo_url
            self._client = MongoClient(self._mongo_url)
            self._db_name = 'barcode'
            self._db = eval('self._client.' + self._db_name)
            self._collection_name = 'rasp_pi_test'
            self._db_colleciton = eval("self._db." + self._collection_name)
            self.push = self.insert_mongo

    def insert_mongo(self):
        """

        """


    def query(self, code_data):
        """

        """
        
        success, res = quer(code_data)
        if success:    
            self._detected_codes.append(code_data)
            return True, res

        else: 
            return False

    
    def push_data(self, data_list):
        """

        """
        rets = []
        for data in data_list:
            event = copy.copy(data)
            event["event_time"] = datetime.datetime.now()
            ret.append(self.push(event))
        return rets
