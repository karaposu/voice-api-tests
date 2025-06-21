# chat_manager.py

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from response_classes import SQLGenerationResult, QueryExecutionResult, ProcessQuestionResult, VisualGenerationResult

from llm_query_executor import LLMQueryExecutor
from llm_visualisation_manager import LLMVisualisationManager


class ChatManager:
    def __init__(self, logger: logging.Logger, allowed_models: Optional[list] = None):
        self.logger = logger
        self.allowed_models = allowed_models or ['gpt-4o-2024-08-06']

        # Initialize the LLMQueryExecutor with the first allowed model
        self.llm_executor = LLMQueryExecutor(
            logger=self.logger,
            yaml_file='assets/prompts.yaml',
            model_name=self.allowed_models[0],
            md_file='assets/database_documentation.md'
        )

        # Initialize the LLMVisualisationManager
        self.visualization_manager = LLMVisualisationManager(
            logger=self.logger,
            yaml_file='assets/prompts.yaml',
            model_name=self.allowed_models[0]
        )

        # Initialize usage information
        self.usage_info = {
            "total_cost": 0.0,
            "query_cost": 0.0,
            "visualization_cost": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            # Additional usage stats...
        }

    def process_message(
            self,
            chat,
            user,
            message: str,
            message_config: Optional[Dict[str, Any]] = None
    ) -> ProcessQuestionResult:
        self.logger.debug("Processing message in ChatManager.")

        # Load message configuration with defaults
      #  message_config = self._load_message_config(message_config)

        # Determine the message type (query or free talk)
        message_type = self.determine_message_type(message, message_config)
        self.logger.debug(f"Message type determined: {message_type}")
        
        chat.message_id += 1
        message_id = chat.message_id
        # message_id = chat.message_id

        # Process the message based on its type
        if message_type == "query":
            self.logger.debug(f"process query")
            return self.process_query(chat, user, message, message_type, message_config, message_id)
        else:
            return self._process_free_talk(chat, user, message, message_type, message_config, message_id)

    def process(self,mob):

        if mob.message_type == "query":
            self.logger.debug(f"process query")
            return self.process_query(chat, user, message, message_type, message_config, message_id)
        else:
            return self._process_free_talk(chat, user, message, message_type, message_config, message_id)


    def process_visualization(
            self,
            chat,
            user,
            query_result: Any,
            query: str,
            visualization_guide: Optional[str] = None,
            message_config: Optional[Dict[str, Any]] = None,
            message_id: Optional[int] = None
    ) -> VisualGenerationResult:
        """
        Processes a visualization request using LLMVisualisationManager.

        If message_id is provided, it updates the corresponding message's visual_code field
        in the chat history with the generated visualization.

        Returns:
            VisualGenerationResult: The result of the visualization process.
        """
        self.logger.debug("Processing visualization request in ChatManager.")

        # Ensure message_id is provided
        if message_id is None:
            self.logger.error("message_id is required to update visualization.")
            return VisualGenerationResult(
                success=False,
                error_message="message_id is required to update visualization."
            )

        # Generate visualization
        result = self.visualization_manager.query_result_to_visual(
            data=query_result,
            query=query,
            visualization_guide=visualization_guide
        )

        # Update usage statistics
        if result.usage_stats:
            visualization_cost = result.usage_stats.get("total_cost", 0.0)
            self._update_usage_info(
                visualization_cost=visualization_cost,
                usage_stats=result.usage_stats
            )

        # Update the corresponding message's visual_code field
        message_entry = chat.chat_history.get_message_by_id(message_id)
        if message_entry is not None:
            if result.success:
                message_entry.visual_code = result.visualization_html
                self.logger.debug(f"Updated message {message_id} with visualization.")
            else:
                self.logger.error(
                    f"Failed to generate visualization for message {message_id}: {result.error_message}"
                )
        else:
            self.logger.error(f"Message with id {message_id} not found in chat history.")
            # Optionally, set the result to unsuccessful if the message is not found
            result.success = False
            result.error_message = f"Message with id {message_id} not found in chat history."

        return result

    # def _load_message_config(self, message_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    #     """
    #     Loads the message configuration, applying defaults where necessary.
    #     """
    #     default_model = self.allowed_models[0] if self.allowed_models else 'gpt-4o-2024-08-06'
    #     default_config = {
    #         "model": default_model,
    #         "free_chat": False,
    #         "use_chat_context_for_sql": False,
    #         "use_chat_context_for_summary": False,
    #         "include_sql_in_chat_context": False,
    #         "include_data_in_chat_context": False,
    #         "history_range_for_context": 5,
    #         "repeat_if_fails": 2,
    #         "do_not_save_to_chat_history": False,
    #         "return_mock_data": False,
    #         "enable_rag_optimization": False,
    #     }
    #     if message_config:
    #         default_config.update(message_config)
    #     self.logger.debug(f"Message configuration loaded: {default_config}")
    #     return default_config

    def determine_message_type(self, message: str, message_config: Dict[str, Any]) -> str:
        """
        Determines the message type using a message type finder or defaults.
        """
        if message_config.get("free_chat", False):
            self.logger.debug("Free chat mode enabled.")
            # Simulate message type determination
            if '?' in message:
                return "query"
            else:
                return "free_talk"
        else:
            return "query"

    def process_query(
            self,
            chat,
            mob,
    ) -> ProcessQuestionResult:
        """
        Processes a query message using LLMQueryExecutor.
        """
        self.logger.debug("Processing query message in ChatManager.")

        # Get context from chat history if needed
        context = None
        if message_config.get("use_chat_context_for_sql", False):
            history_range = message_config.get("history_range_for_context", 5)
            include_sql = message_config.get("include_sql_in_chat_context", False)
            include_data = message_config.get("include_data_in_chat_context", False)

            exclude_fields = []
            if not include_sql:
                exclude_fields.append("sql")
            if not include_data:
                exclude_fields.append("data")

            selected_history = chat.chat_history.get_last_n_elements(
                n=history_range,
                exclude_fields=exclude_fields if exclude_fields else None
            )
            context = chat.chat_history.stringify_history(selected_history)
            self.logger.debug(f"Context for query: {context}")

        # Process the question using LLMQueryExecutor
        result = self.llm_executor.process_question(
            user_question=message,
            context=context,
            request_config=message_config
        )

        result.message_id = message_id
        result.message_type=message_type

        self.logger.debug("result : %s", result)

        # Update usage statistics
        if result.usage_stats:
            query_cost = result.usage_stats.get("total_cost", 0.0)
            self._update_usage_info(query_cost=query_cost, usage_stats=result.usage_stats)

        # Optionally log the SQL query
        if result.sql_generation_result and result.sql_generation_result.sql_query:
            self.logger.debug(f"Generated SQL Query: {result.sql_generation_result.sql_query}")

        # Optionally include the SQL query in the result data
        if result.success and result.data is not None:
            result.data['sql_query'] = result.sql_generation_result.sql_query

        return result

    def _process_free_talk(
            self,
            chat,
            user,
            message: str,
            message_type,
            message_config: Dict[str, Any],
            message_id: int  # Ad
    ) -> ProcessQuestionResult:
        """
        Processes a free talk message.
        """
        self.logger.debug("Processing free talk message in ChatManager.")
        model = message_config.get("model", "gpt-4o-mini")

        # Simulate a response for free talk
        response_text = f"Let's chat! You said: {message}"

        # Simulate usage stats
        usage_stats = {
            "total_cost": 0.005,  # Simulated cost
            "input_tokens": len(message.split()),
            "output_tokens": len(response_text.split()),
            "model_name": model
        }

        # Update usage statistics
        self._update_usage_info(usage_stats=usage_stats)

        result_data = {
            "answer": response_text,
            "message_type": "free_talk",
            "model": model
        }
        # return ProcessQuestionResult(
        #     success=True,
        #     data=result_data,
        #     usage_stats=usage_stats,
        #     message_id=message_id  # Include message_id
        # )

        return ProcessQuestionResult(
            success=True ,
            data =result_data,
            visual_code =None ,
            usage_stats =usage_stats ,
            error_message =None,
            sql_generation_result =None ,
            query_execution_result =None  ,
            message_id  =message_id ,
            message_type  =message_type ,
        )


    def _update_usage_info(self, query_cost: float = 0.0, visualization_cost: float = 0.0,
                           usage_stats: Dict[str, Any] = None):
        """
        Updates the cumulative usage information based on the usage stats.
        """
        if usage_stats is None:
            usage_stats = {}

        self.logger.debug(f"Updating usage info with: {usage_stats}")
        
        # Update total cost
        total_cost = usage_stats.get("total_cost", 0.0)
        self.usage_info["total_cost"] += total_cost

        # Update specific costs
        if query_cost > 0:
            self.usage_info["query_cost"] += query_cost
        if visualization_cost > 0:
            self.usage_info["visualization_cost"] += visualization_cost

        # Update token counts
        self.usage_info["total_input_tokens"] += usage_stats.get("input_tokens", 0)
        self.usage_info["total_output_tokens"] += usage_stats.get("output_tokens", 0)

        # Additional usage stats can be updated here
