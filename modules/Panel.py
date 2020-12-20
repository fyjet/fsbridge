import time

class Panel(object):
    """Parent object for all panels"""
    def __init__(self, client):
        self.client=client
        # logger.debug("Panel class initialized")

    def mqttpublish(self, topic, payload):
        global alivetime

        self.client.publish(topic,payload)
        self.alivetime=time.time()   # the keepalive ticker