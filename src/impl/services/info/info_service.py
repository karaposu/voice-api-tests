from .base_service import BaseService
from datetime import datetime


from indented_logger import IndentedLogger
import logging
logger_setup = IndentedLogger(name='upload_pdf', level=logging.DEBUG, log_file=None)
logger = logger_setup.get_logger()


def get_current_time():
    return datetime.utcnow()


from llm_visualisation_manager import LLMVisualisationManager
from chat import ChatUser



class InfoService(BaseService):
    def check_compatibility(self, img=None, text=None):
        return True, ""

    # def initialize_db_manager(self):
    #     db_path = os.path.join(os.path.dirname(__file__), "..", "..", "budget_tracker.db")
    #     db_path = os.path.abspath(db_path)
    #     if not os.path.exists(db_path):
    #         raise FileNotFoundError(f"Database file not found at: {db_path}")
    #     if not os.access(db_path, os.W_OK):
    #         raise PermissionError(f"Database file is not writable: {db_path}")
    #
    #     try:
    #         return DBManager(db_path)
    #     except Exception as e:
    #         raise RuntimeError(f"Failed to initialize DBManager: {e}")


    def preprocess_request_data(self):


        new_chat=self.dependencies.new_chat()

        response = new_chat.generate_cost_summary()

        self.preprocessed_data=response

    def process_request(self):
        self.response=self.preprocessed_data



class VisualizeService(BaseService):
    def check_compatibility(self, img=None, text=None):
        return True, ""

    # def initialize_db_manager(self):
    #     db_path = os.path.join(os.path.dirname(__file__), "..", "..", "budget_tracker.db")
    #     db_path = os.path.abspath(db_path)
    #     if not os.path.exists(db_path):
    #         raise FileNotFoundError(f"Database file not found at: {db_path}")
    #     if not os.access(db_path, os.W_OK):
    #         raise PermissionError(f"Database file is not writable: {db_path}")
    #
    #     try:
    #         return DBManager(db_path)
    #     except Exception as e:
    #         raise RuntimeError(f"Failed to initialize DBManager: {e}")


    def preprocess_request_data(self):


        new_chat=self.dependencies.new_chat()

        # data: Optional[StrictStr] = None
        # query: Optional[StrictStr] = None
        # background: Optional[StrictStr] = None
        # visualization_guide: Optional[StrictStr] = None

        llmvis = LLMVisualisationManager()

        # logger.debug(f" type(request.data)", type(request.data))
        # logger.debug(f" type(request.query)", type(request.query))

        llm_generated_html , llm_request_success= llmvis.query_result_to_visual(self.request.data, self.request.query, self.request.background,  self.request.visualization_guide)
        #return llm_generated_html


        #cu = ChatUser("user", ["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"], "all", False)

        # Example response
        response=llm_generated_html
        # response = {
        #     "llm_request_success":llm_request_success,
        #     "answer": answer,
        #     "sql": sql,
        #     "error": error,
        #     "visual_type": extra,
        #     "usage": info_dict
        # }

        self.preprocessed_data=response

    def process_request(self):
        self.response=self.preprocessed_data