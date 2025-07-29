# here is myllmservice.py

import logging

# logger = logging.getLogger(__name__)
import asyncio
from llmservice import BaseLLMService, GenerationRequest, GenerationResult
from typing import Optional, Union
from . import prompts


class MyLLMService(BaseLLMService):
    def __init__(self, logger=None, max_concurrent_requests=200):
        super().__init__(
            logger=logging.getLogger(__name__),
            # default_model_name="gpt-4o-mini",
            default_model_name="gpt-4.1-nano",
            max_rpm=500,
            max_concurrent_requests=max_concurrent_requests,
        )
       
    # def filter, parse


   

    def generate_ai_answer(self, chat_history: str, user_msg=None, model = None,
    ) -> GenerationResult:
        
        formatted_prompt = prompts.GENERATE_AI_ANSWER_PROMPT.format(
            chat_history=chat_history,
            user_msg=user_msg
        )
       
        
        if model is None:
            model= "gpt-4o-mini"

        generation_request = GenerationRequest(
            formatted_prompt=formatted_prompt,
            model=model,
            output_type="str",
            operation_name="generate_ai_answer",
            # pipeline_config=pipeline_config,
            # request_id=request_id,
        )

        result = self.execute_generation(generation_request)
        return result
    
    def generate_affirmations_with_llm(self, context: str, category: Optional[str] = None, 
                                     count: int = 5, model: Optional[str] = None) -> GenerationResult:
        """
        Generate positive affirmations based on user context using LLM.
        
        Args:
            context: The user's context/situation for generating relevant affirmations
            category: Optional category for the affirmations
            count: Number of affirmations to generate (default: 5)
            model: LLM model to use (default: gpt-4o-mini)
            
        Returns:
            GenerationResult containing the generated affirmations
        """
        category_line = f'Category: {category}' if category else ''
        formatted_prompt = prompts.GENERATE_AFFIRMATIONS_PROMPT.format(
            count=count,
            context=context,
            category_line=category_line
        )

        if model is None:
            model = "gpt-4o-mini"
        
        generation_request = GenerationRequest(
            formatted_prompt=formatted_prompt,
            model=model,
            output_type="json",
            operation_name="generate_affirmations"
        )
        
        result = self.execute_generation(generation_request)
        return result
    


   


def main():
    """
    Main function to test the categorize_simple method of MyLLMService.
    """
    # Initialize the service
    my_llm_service = MyLLMService()

    # Sample data for testing
    sample_record = "The company reported a significant increase in revenue this quarter."
    sample_classes = ["Finance", "Marketing", "Operations", "Human Resources"]
    request_id = 1

    try:
        # Perform categorization
        result = my_llm_service.categorize_simple(
            record=sample_record,
            list_of_classes=sample_classes,
            request_id=request_id
        )

        # Print the result
        print("Generation Result:", result)
        if result.success:
            print("Categorized Content:", result.content)
        else:
            print("Error:", result.error_message)
    except Exception as e:
        print(f"An exception occurred: {e}")


if __name__ == "__main__":
    main()
