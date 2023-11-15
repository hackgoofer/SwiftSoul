import openai
import chroma


class RetrievalInterface:
    def store(self, data):
        raise NotImplementedError

    def retrieve(self, key):
        raise NotImplementedError


class RetrievalDB(RetrievalInterface):
    def __init__(self):
        self.db = {}

    def store(self, data):
        self.db[data["key"]] = data["value"]

    def retrieve(self, key):
        return self.db.get(key, None)


class RetrievalGPT(RetrievalInterface):
    def __init__(self):
        self.gpt = {}

    def store(self, data):
        self.gpt[data["key"]] = data["value"]

    def retrieve(self, key):
        return self.gpt.get(key, None)
