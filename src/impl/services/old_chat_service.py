# from .base_service import BaseService
from datetime import datetime



import logging
logger = logging.getLogger(__name__)


import tempfile
import os

def get_current_time():
    return datetime.utcnow()



class ChatRetrieverService:
    def check_compatibility(self, img=None, text=None):
        return True, ""

    def preprocess_request_data(self):

        new_chat=self.dependencies.new_chat()

        # history
        # logger
        # history = new_chat.chat_history.history
        history=new_chat.get_history()

        # new_form=[]
        # for e in history:
        #
        #     {user_id}
        #     new_form.append()


        # user_id: Optional[StrictStr] = None
        # message_id: Optional[StrictStr] = None
        # message: Optional[StrictStr] = None
        # who: Optional[StrictStr] = None
        # message_date: Optional[datetime] = None
        # data: Optional[HistoryMessageData] = None
        # __properties: ClassVar[List[str]] = ["user_id", "message_id", "message", "who", "message_date", "data"]

        self.preprocessed_data=history

    def process_request(self):
        self.response=self.preprocessed_data


class ChatMetaDataRetrieverService(BaseService):
    def check_compatibility(self, img=None, text=None):
        return True, ""

    def preprocess_request_data(self):
        new_chat = self.dependencies.new_chat()
        r={"chat_name": new_chat.chat_name ,
        "creation": new_chat.creation ,
        "attached_db_name": new_chat.attached_db_name}

        self.preprocessed_data = r

    def process_request(self):
        self.response = self.preprocessed_data



