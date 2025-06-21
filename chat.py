# chat.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import copy
from chat_manager import ChatManager  # Ensure this module is available in your project
from response_classes import VisualGenerationResult, ProcessQuestionResult
import yaml
from response_classes import  ChatUser, MessageEntry
from chat_histroy import ChatHistory
from usage_stats import UsageStats
from generation_engine import GenerationEngine



from indented_logger import IndentedLogger, log_indent
import logging
#
# # Setup the logger with function names included
# logger_setup = IndentedLogger(name='my_logger', level=logging.DEBUG, include_func=True)
# my_logger = logger_setup.get_logger()


from indent import  IndentedLogger
indented_logger = IndentedLogger('my_logger', include_func=True, truncate_messages=False, min_func_name_col=100)
my_logger = indented_logger.get_logger()



def indent_log_pretty(logger_object, dictonary, lvl, exclude=[]):
    for key, value in dictonary.items():
        if key not in exclude:
            if isinstance(value, list):
                logger_object.debug(f"{key}: %s length: ", {len(value)}, lvl=lvl)
            else:
               logger_object.debug(f"{key}: %s", {value}, lvl=lvl)



# Define the Chat class
class Chat:
    def __init__(
        self,
        users: List[ChatUser],
        allowed_models: List[str],
        logger =None,
        configs: Optional[Dict[str, Any]] = None,
    ):
        self.chat_name = "Test TeamProcure"
        self.creation = datetime.now().isoformat()
        self.attached_db_name = "Test Database"

        self.logger = logger if logger else my_logger

        self.logger.info('Chat Initializing', lvl=0)
        self.users = users.copy()
        self.allowed_models = allowed_models
        self.chat_history = ChatHistory()
        self.configs = configs or {}
        self.message_id = 0
        self.last_message_id = 0

        self.query_usage_stats= UsageStats()
        self.visualisation_usage_stats = UsageStats()
        self.nonquery_usage_stats = UsageStats()


        md_file = 'assets/database_documentation.md'
        try:
            with open(md_file, 'r', encoding='utf-8') as file:
                self.md_content = file.read()
        except FileNotFoundError:
            self.logger.exception(f"Markdown file {md_file} not found.")
            raise

        self.logger.info('Document is read. Total char: %s',len(self.md_content) , lvl=1)

        self.generation_engine= GenerationEngine(logger=self.logger)
        self.logger.info('generation_engine initialized', lvl=1)

        allowed_models = ["gpt-4o", "gpt-4o-2024-08-06", "gpt-4o-mini", "o1-preview", "o1-mini"]
        allowed_actions = ["all"]
        credit_limit = False

        self.default_ai_user = ChatUser(id=999, name="ai", type="ai", allowed_models=allowed_models,allowed_actions=allowed_actions, credit_limit=credit_limit)
        self.logger.info('  ')
        self.logger.info('  ')

    def load_models(self):
        yaml_file_path = "assets/model_info.yaml"

        with open(yaml_file_path, 'r') as file:
            models_data = yaml.safe_load(file)

        self.models = models_data.get("models", {})
        defaults = models_data.get("defaults", {})

        for attr, model_name in defaults.items():
            setattr(self, attr, model_name)


    def attach_new_logger(self, l):
        self.logger=l
        self.generation_engine.logger=l

    def get_new_unique_id(self):

        self.last_message_id += 1

        return self.last_message_id

    def _load_message_config(self, message_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Loads the message configuration, applying defaults where necessary.
        """
        default_model = self.allowed_models[0] if self.allowed_models else 'gpt-4o-2024-08-06'
        default_config = {
            "model": default_model,
            "free_chat": False,
            "use_chat_context_for_sql": False,
            "use_chat_context_for_summary": False,
            "include_sql_in_chat_context": False,
            "include_data_in_chat_context": False,
            "history_range_for_context": 5,
            "repeat_if_fails": 2,
            "do_not_save_to_chat_history": False,
            "return_mock_data": False,
            "enable_rag_optimization": False,
            "pick_model_for_visualisation": default_model,
            "pick_model_for_summary": default_model,
            "pick_model_for_ai_chat": default_model,
            "pick_model_for_message_type_checker": default_model,

        }
        if message_config:
            default_config.update(message_config)
        self.logger.debug(f"Message configuration loaded", lvl=2)
        indent_log_pretty(self.logger, default_config, lvl=3)

        return default_config

    def create_new_message_obj(self, user, message, message_config=None, ai=False):

        config=self._load_message_config(message_config)

        if ai:
            mob = MessageEntry(
                id=self.get_new_unique_id(),
                user_name=user.name,
                user_type="ai",
                user_id=999,
                message=message,
                message_type=None,
                model=None,
                sql=None,
                sql_result=None,
                visual_code=None,
                context=None,
                message_config=config,
            )

            return mob

        mob= MessageEntry(
                            id= self.get_new_unique_id(),
                            user_name=user.name,
                            user_type=user.type,
                            user_id=0,
                            message= message,
                            message_type=None,
                            model= None,
                            sql= None,
                            sql_result=None,
                            visual_code=None,
                            context=None,
                            message_config=config,
                            )

        mob.usage_stats = UsageStats()

        return mob


    def generate_cost_summary(self):
        return {
            "query_creation_cost": self.query_usage_stats.total_cost,
            "non_query_creation_cost": self.nonquery_usage_stats.total_cost,
            "visualization_cost": self.visualisation_usage_stats.total_cost,
            "total_cost": round(
                self.query_usage_stats.total_cost
                + self.nonquery_usage_stats.total_cost
                + self.visualisation_usage_stats.total_cost,
                5
            )
        }



    def merge_usage_dicts(self,main_dict, update_dict):



        main_dict["input_tokens"] += update_dict.get("input_tokens", 0)
        main_dict["output_tokens"] += update_dict.get("output_tokens", 0)
        main_dict["total_tokens"] += update_dict.get("total_tokens", 0)
        main_dict["input_cost"] += update_dict.get("input_cost", 0.0)
        main_dict["output_cost"] += update_dict.get("output_cost", 0.0)
        main_dict["total_cost"] += update_dict.get("total_cost", 0.0)

        return main_dict
       # self.total_cost = round(self.total_cost, 5)



    def _handle_ai_message(self, user, message):

        mob=self.create_new_message_obj(user, message, ai=True)
        self.chat_history.add_message(mob.__dict__)

    def input_a_message(self, user: ChatUser, message ,message_config ) -> ProcessQuestionResult:


        self.logger.info('input message: %s',message , lvl=1)
        self.logger.info('input message config:', lvl=2)
        indent_log_pretty(self.logger, message_config, lvl=3)

        if user.type == "ai":
            self.logger.info('it is an AI response message', lvl=2)

            self._handle_ai_message(user, message)
            return

        # per_message_usage_stats = UsageStats()
        mob=self.create_new_message_obj(user,message ,message_config)
        self.logger.info('Message object created', lvl=2)
        # mob.usage_stats= per_message_usage_stats

        # message_type_generation_result =self.generation_engine.determine_message_type(mob.message, prefered_model=mob.message_config["pick_model_for_message_type_checker"])
        # mob.message_type=  message_type_generation_result.content
        # self.logger.info('Message type: %s ', mob.message_type, lvl=2)
        # self.logger.info('message_type calculation cost: %s ', message_type_generation_result.meta["total_cost"], lvl=3)


        # self.nonquery_usage_stats.update(message_type_generation_result.meta)
        # self.logger.info('----> cost_summary(): %s ', self.generate_cost_summary(), lvl=2)

        # mob.usage_stats.update(message_type_generation_result.meta)

        # self.logger.info('----> mob.usage_stats: %s ', mob.usage_stats.to_dict(), lvl=2)

        # self.logger.info('entering mob_processor() %s ', mob.message_type, lvl=2)

        process_result =self.mob_processor(mob)

        # self.logger.info('process_result %s ', process_result, lvl=2)



        self.chat_history.add_message(mob.__dict__)

        return process_result

    def mob_processor(self, mob):

        if mob.message_config.get("free_chat", False):
            message_type_generation_result = self.generation_engine.determine_message_type(mob.message)
            mob.message_type = message_type_generation_result.content
            self.nonquery_usage_stats.update(message_type_generation_result.meta)
            mob.usage_stats.update(message_type_generation_result.meta)
        else:
            mob.message_type = "query"



        self.logger.info('----> cost_summary(): %s ', self.generate_cost_summary(), lvl=2)




        self.logger.debug(f"Message Type is %s ", mob.message_type, lvl=3)

        if mob.message_type == "query":

                process_question_result=self.process_query(mob)

                #self.logger.info(' .... process_question_result usage: %s ', process_question_result.usage_stats, lvl=2)
                # 0.13

                self.query_usage_stats.update(process_question_result.sql_generation_result.meta)
               # self.logger.info('2----> cost_summary(): %s ', self.generate_cost_summary(), lvl=2)
                mob.usage_stats.update(process_question_result.sql_generation_result.meta)

               # self.logger.info('2----> mob.usage_stats: %s ', mob.usage_stats.to_dict(), lvl=2)

                process_question_result.usage_stats= process_question_result.sql_generation_result.meta

                #process_question_result.usage_stats = self.merge_usage_dicts(process_question_result.usage_stats,   process_question_result.sql_generation_result.meta)
                self.logger.info(' 2.... process_question_result usage: %s ', process_question_result.usage_stats, lvl=2)


                mob.sql = process_question_result.sql_generation_result.content
                if process_question_result.query_execution_result.success:
                    mob.sql_result = process_question_result.query_execution_result.data["rows"]
                    mob.sql_result_row_count = process_question_result.query_execution_result.data["row_count"]

                    summary_generation_result = self.summary_maker(mob)
                    self.logger.debug(f"Generated Summary  %s ",summary_generation_result.content,  lvl=3)
                    self.nonquery_usage_stats.update(summary_generation_result.meta)
                   # self.logger.info('3----> cost_summary(): %s ', self.generate_cost_summary(), lvl=2)

                    #process_question_result.usage_stats.update(summary_generation_result.meta)

                    process_question_result.usage_stats = self.merge_usage_dicts(process_question_result.usage_stats, summary_generation_result.meta)
                    mob.summary= summary_generation_result.content
                    self.input_a_message(self.default_ai_user,  summary_generation_result.content, {} )

                self.logger.debug(f"mob after process_query: ", lvl=3)
                indent_log_pretty(self.logger, mob.__dict__, lvl=4, exclude=["message_config"])

                if mob.message_config.get("free_chat", False):
                    process_question_result.usage_stats = self.merge_usage_dicts(process_question_result.usage_stats,
                                                                        message_type_generation_result.meta)

                return process_question_result

        else:
                process_question_result=self.process_non_query(mob)
                self.nonquery_usage_stats.update(process_question_result.non_query_talk_result.meta)

                process_question_result.usage_stats = self.merge_usage_dicts(process_question_result.usage_stats,
                                                                             message_type_generation_result.meta)

                return process_question_result


    def process_non_query( self,mob ) -> ProcessQuestionResult:
        """
        Processes a free talk message.
        """
        self.logger.debug("Processing free talk message in ChatManager.")
        model = mob.message_config.get("model", "gpt-4o-mini")

        history_range = mob.message_config.get("history_range_for_context", 5)
        include_sql = mob.message_config.get("include_sql_in_chat_context", False)
        include_data = mob.message_config.get("include_data_in_chat_context", False)

        exclude_fields = []
        if not include_sql:
            exclude_fields.append("sql")
        if not include_data:
            exclude_fields.append("data")

        selected_history = self.chat_history.get_last_n_elements(
            n=history_range,
            exclude_fields=exclude_fields if exclude_fields else None
        )
        context = self.chat_history.stringify_history(selected_history)
        # self.logger.debug(f"Context for query: {context}")

        generation_result =self.generation_engine.no_query_talk(mob, self.md_content, context)

        self.nonquery_usage_stats.update(generation_result.meta)

        return ProcessQuestionResult(success=True,
                              non_query_talk_result= generation_result,
                              message_id= mob.id,
                              message_type= mob.message_type
        )


    def get_history(self, num_messages: int = None) -> List[dict]:

        self.logger.debug(" ")

        self.logger.debug(">>>>>>>>>>>>>>>inside get_history")

        r=self.chat_history.get_history(num_messages)

        self.logger.debug("history: %s", r)

        return  r

    def get_chat_summary(self) -> str:
        """
        Returns a stringified version of the entire chat history.
        """
        messages = self.chat_history.get_history()
        return self.chat_history.stringify_history(messages)

    def clear_chat_history(self):
        """
        Clears the chat history.
        """
        self.chat_history.clear_history()
        self.message_id = 0
        self.logger.debug("Chat history cleared.")

    def add_user(self, user: ChatUser):
        """
        Adds a new user to the chat.
        """
        if user not in self.users:
            self.users.append(user)
            self.logger.debug(f"User {user.name} added to the chat.")
        else:
            self.logger.debug(f"User {user.name} already in the chat.")

    def remove_user(self, user: ChatUser):
        """
        Removes a user from the chat.
        """
        if user in self.users:
            self.users.remove(user)
            self.logger.debug(f"User {user.name} removed from the chat.")


    def update_message_by_id(self, message_id,field_name ,value):

        for e in  self.chat_history.history:
            if e["id"]==message_id:
                e[field_name]=value


    def run_html_code_size_reducer(self, code, new_size):

        generation_result = self.generation_engine.process_html_code_size_reducer(code, new_size)

        return generation_result

    def run_visualisation(self, query_result , query, visualization_guide, message_id, name_of_model):


        generation_result= self.generation_engine.process_visualization(query_result , query, visualization_guide, name_of_model=name_of_model)
        self.visualisation_usage_stats.update(generation_result.meta)

        self.update_message_by_id(message_id,"visual_code" , generation_result.content  )

        # if generation_result.success:
        #     new_size= "Height 140px"
        #     size_reducer_generation_result=self.run_html_code_size_reducer( generation_result.content, new_size=new_size)
        #     if size_reducer_generation_result.success:
        #         self.visualisation_usage_stats.update(size_reducer_generation_result.meta)
        #         self.update_message_by_id(message_id, "visual_code_mini", size_reducer_generation_result.content)

        return generation_result


    def summary_maker(self,mob):

        merged_history_string = None

        if hasattr(mob, 'sql_result_row_count') and mob.sql_result_row_count is not None and mob.sql_result_row_count > 500:
            data = None  # Do not include data if too large

        # if mob.sql_result_row_count > 500:
        #
        #     data = None  # Do not include data if too large

        if mob.message_config.get("use_chat_context_for_sql", False):
            history_range = mob.message_config.get("history_range_for_context", 5)
            include_sql = mob.message_config.get("include_sql_in_chat_context", False)
            include_data = mob.message_config.get("include_data_in_chat_context", False)

            exclude_fields = []
            if not include_sql:
                exclude_fields.append("sql")
            if not include_data:
                exclude_fields.append("data")

            # Get the last n elements from chat history
            selected_history = self.chat_history.get_last_n_elements(n=history_range, exclude_fields=exclude_fields)
            merged_history_string = self.chat_history.stringify_history(selected_history)


        summary_generation_response = self.generation_engine.create_summary(mob, merged_history_string)


        # self.logger.info('summary usage:', lvl=2)
        self.logger.info('summary calculation cost: %s ', summary_generation_response.meta["total_cost"], lvl=3)

        indent_log_pretty(self.logger, summary_generation_response.meta, lvl=2)

        # self.logger.info('Message type: %s ', mob.message_type, lvl=2)
        # self.logger.info('message_type calculation cost: %s ', summary_generation_response.meta["total_cost"], lvl=3)

        return summary_generation_response
        # content, success, meta = self.airp.create_summary(mob, context)

    def process_query(self,mob) -> ProcessQuestionResult:
        """
        Processes a query message using LLMQueryExecutor.
        """


        self.logger.info('Processing query message ' , lvl=3)
        # self.logger.info('Processing query message %s ', mob.message_type, lvl=3)

        # Get context from chat history if needed
        context = None
        if mob.message_config.get("use_chat_context_for_sql", False):

            self.logger.debug("use_chat_context_for_sql is True", lvl=3)

            history_range = mob.message_config.get("history_range_for_context", 5)
            include_sql = mob.message_config.get("include_sql_in_chat_context", False)
            include_data = mob.message_config.get("include_data_in_chat_context", False)

            exclude_fields = []
            if not include_sql:
                exclude_fields.append("sql")
            if not include_data:
                exclude_fields.append("data")

            selected_history = self.chat_history.get_last_n_elements(
                n=history_range,
                exclude_fields=exclude_fields if exclude_fields else None
            )

            context = self.chat_history.stringify_history(selected_history)
            # self.logger.debug(f"Context for query: {context}")


        self.logger.debug("entering execute_sql_with_feedback", lvl=3)
        # self.logger.debug(" len self.md_content: %s ", len(self.md_content))

       # if mob.message_config.get("enable_rag_optimization") and mob.message_config.get("model") == "gpt-4o-2024-08-06":
        if mob.message_config.get("enable_rag_optimization"):

            relevant_tables_generation_result= self.generation_engine.relevant_table_identifier(mob.message, self.md_content)
            self.logger.debug("relevant_tables_generation_result %s", relevant_tables_generation_result.content, lvl=3)

            from my_ai_tools.generation_manager import string_to_dict
            data_dict= string_to_dict(relevant_tables_generation_result.content)
            table_list = list(data_dict.values())

            self.logger.debug("data %s", table_list, lvl=3)

            self.logger.debug("len self.md_content %s", len(self.md_content), lvl=3)
            trimmed_md_content=self.generation_engine.document_trimmer(self.md_content, table_list)
            self.logger.debug("len trimmed_md_content %s", len(trimmed_md_content), lvl=3)



            process_question_result = self.generation_engine.execute_sql_with_feedback( mob=mob,
                                                                                        context=context ,
                                                                                        md_content=trimmed_md_content )
        else:
            process_question_result = self.generation_engine.execute_sql_with_feedback(mob=mob,
                                                                                       context=context,
                                                                                       md_content=self.md_content)

        return process_question_result




# Usage example
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("ChatLogger")


    # Context for query

    # Create users
    user1 = ChatUser(name="enes", allowed_models=["gpt-4o", "gpt-4o-mini"], user_type="human")

    # Initialize chat
    allowed_models = ["gpt-4o"]
    chat = Chat(users=[user1], allowed_models=allowed_models, logger=logger)

    # Define message configuration
    input_message_config = {
        "free_chat": True,
        "use_context_for_sql": True,
        "use_context_for_summary": True,
        "repeat_if_fails": 5,
        "model": "gpt-4o",
        "timestamp": datetime.now().isoformat(),
    }

    # User sends a message
    message = "En cok para harcadigimiz 3 tedarikci kim?"
    result = chat.input_a_message(user1, message, input_message_config)

    # Print the result and usage stats
    if result.success:
        print("Message processed successfully.")
        print("Result data:", result.data)
        print("Usage stats for this message:", result.usage_stats)
    else:
        print("Error processing message:", result.error_message)

    # Access cumulative usage info via Chat method
    cumulative_usage = chat.get_cumulative_usage_info()
    print("Cumulative usage info:")
    print(cumulative_usage)

    # Get chat history
    history = chat.get_history()

    print(" ")
    print("Chat History:")

    
    for entry in history:
        print(entry)


    


