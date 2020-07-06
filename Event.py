class Event(object):
    "event class to bufferize events"
    def __init__(self):
        self.__topic=""
        self.__payload=""
    
    def set(self,topic,payload):
        self.__topic=topic
        self.__payload=payload
        
    def getTopic(self):
        return self.__topic
    
    def getPayload(self):
        return self.__payload
    
    def isEmpty(self):
        return (self.__topic=="")
    
    def clear(self):
        self.__topic=""
        self.__payload=""