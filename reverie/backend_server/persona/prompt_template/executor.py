import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from infra.llm import LLMService
from persona.prompt_template.prompts import BasePrompt

logger = logging.getLogger(__name__)

class PromptExecutor:
    """
    Executes prompts using the LLMService, handling prompt generation,
    execution, validation, and cleanup.
    """
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, 
                prompt: BasePrompt, 
                test_input: Any = None, 
                model: str = "gpt-3.5-turbo",
                temperature: float = 0.7,
                max_tokens: Optional[int] = None,
                max_retries: int = 3,
                **kwargs) -> Any:
        """
        Executes a prompt.

        Args:
            prompt: The prompt instance to execute.
            test_input: Optional input to override the prompt's default input generation.
            model: The LLM model to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            max_retries: Number of retries for validation failures.
            **kwargs: Additional arguments for the LLM provider.

        Returns:
            The processed output from the prompt.
        """
        
        # Check if this is a new-style prompt
        is_new_style = hasattr(prompt, 'input_schema') and hasattr(prompt, 'render_prompt')
        
        # 1. Generate the prompt text
        prompt_text = self._generate_prompt_text(prompt, test_input)
        
        # 2. Determine execution mode (Chat vs Completion)
        # For now, we infer based on the presence of example_output/special_instruction
        # or if the model is a known chat model.
        
        is_chat_model = ("gpt-3.5" in model or "gpt-4" in model) and "instruct" not in model
        
        # For new-style prompts, use simple completion/chat since they handle output parsing via Pydantic
        if is_new_style:
            if is_chat_model:
                return self._execute_new_style_chat(
                    prompt_text, 
                    prompt, 
                    test_input,
                    model, 
                    temperature, 
                    max_tokens, 
                    max_retries, 
                    **kwargs
                )
            else:
                return self._execute_new_style_completion(
                    prompt_text, 
                    prompt, 
                    test_input,
                    model, 
                    temperature, 
                    max_tokens, 
                    max_retries, 
                    **kwargs
                )
        
        # Legacy prompts - check for example_output/special_instruction
        if hasattr(prompt, 'example_output') and hasattr(prompt, 'special_instruction') and \
           prompt.example_output is not None and prompt.special_instruction is not None:
            return self._execute_chat_safe(
                prompt_text, 
                prompt, 
                model, 
                temperature, 
                max_tokens, 
                max_retries, 
                **kwargs
            )
        else:
            # Legacy completion or simple chat
            if is_chat_model:
                return self._execute_chat_simple(
                    prompt_text, 
                    prompt, 
                    model, 
                    temperature, 
                    max_tokens, 
                    max_retries, 
                    **kwargs
                )
            else:
                return self._execute_completion(
                    prompt_text, 
                    prompt, 
                    model, 
                    temperature, 
                    max_tokens, 
                    max_retries, 
                    **kwargs
                )

    def _generate_prompt_text(self, prompt_instance: BasePrompt, test_input: Any = None) -> str:
        """
        Generates the raw prompt text by filling in the template.
        Supports both new schema-based prompts (with render_prompt) and 
        legacy prompts (with create_prompt_input + prompt_template file).
        """
        # Check if this is a new-style prompt with render_prompt method and input_schema
        if hasattr(prompt_instance, 'input_schema') and hasattr(prompt_instance, 'render_prompt'):
            # New schema-based prompt
            if test_input is not None:
                # test_input should be the input schema instance or dict
                if isinstance(test_input, dict):
                    input_data = prompt_instance.input_schema(**test_input)
                else:
                    input_data = test_input
            else:
                # For new prompts, input must be provided via test_input
                raise ValueError(f"New-style prompts require input data. Pass input via test_input parameter.")
            return prompt_instance.render_prompt(input_data)
        
        # Legacy prompt with create_prompt_input and prompt_template file
        prompt_input = prompt_instance.create_prompt_input(test_input)
        
        # Logic adapted from gpt_structure.generate_prompt
        if isinstance(prompt_input, str):
            prompt_input = [prompt_input]
        prompt_input = [str(i) for i in prompt_input]

        # We assume prompt_template is a file path relative to the project root or current working dir
        # In the original code, it opens the file directly.
        # We might need to handle paths better.
        try:
            with open(prompt_instance.prompt_template, "r") as f:
                prompt_text = f.read()
        except FileNotFoundError:
            # Try prepending the project root or similar if needed
            # For now, assume the path is correct as per original code
            raise

        for count, i in enumerate(prompt_input):   
            prompt_text = prompt_text.replace(f"!<INPUT {count}>!", i)
        
        if "<commentblockmarker>###</commentblockmarker>" in prompt_text: 
            prompt_text = prompt_text.split("<commentblockmarker>###</commentblockmarker>")[1]
            
        return prompt_text.strip()

    def _execute_chat_safe(self, 
                           prompt_text: str, 
                           prompt_instance: BasePrompt, 
                           model: str, 
                           temperature: float, 
                           max_tokens: Optional[int], 
                           max_retries: int,
                           **kwargs) -> Any:
        
        # Construct the "safe" prompt wrapper (JSON enforcement)
        # This logic mimics ChatGPT_safe_generate_response
        wrapped_prompt = f'"""\n{prompt_text}\n"""\n'
        wrapped_prompt += f"Output the response to the prompt above in json. {prompt_instance.special_instruction}\n"
        wrapped_prompt += "Example output json:\n"
        wrapped_prompt += f'{{"output": "{str(prompt_instance.example_output)}"}}'

        messages = [{"role": "user", "content": wrapped_prompt}]

        for i in range(max_retries + 1):
            try:
                response_content = self.llm_service.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Parse JSON
                response_content = response_content.strip()
                # Attempt to extract JSON if it's wrapped in other text
                try:
                    end_index = response_content.rfind('}') + 1
                    if end_index > 0:
                        response_content = response_content[:end_index]
                    parsed_json = json.loads(response_content)
                    output = parsed_json["output"]
                except (json.JSONDecodeError, KeyError):
                    # If parsing fails, maybe the model just outputted the text?
                    # But the prompt explicitly asks for JSON.
                    # Let's try to validate the raw content if JSON fails? 
                    # Original code assumes it MUST be JSON.
                    output = response_content

                if prompt_instance.validate(output, prompt=wrapped_prompt):
                    return prompt_instance.clean_up(output, prompt=wrapped_prompt)
                
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        return prompt_instance.get_fail_safe()

    def _execute_chat_simple(self, 
                             prompt_text: str, 
                             prompt_instance: BasePrompt, 
                             model: str, 
                             temperature: float, 
                             max_tokens: Optional[int], 
                             max_retries: int,
                             **kwargs) -> Any:
        
        messages = [{"role": "user", "content": prompt_text}]

        for i in range(max_retries + 1):
            try:
                response_content = self.llm_service.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if prompt_instance.validate(response_content, prompt=prompt_text):
                    return prompt_instance.clean_up(response_content, prompt=prompt_text)
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
                
        return prompt_instance.get_fail_safe()

    def _execute_completion(self, 
                            prompt_text: str, 
                            prompt_instance: BasePrompt, 
                            model: str, 
                            temperature: float, 
                            max_tokens: Optional[int], 
                            max_retries: int,
                            **kwargs) -> Any:
        
        for i in range(max_retries + 1):
            try:
                # We need to access the provider directly or add completion to LLMService
                # LLMService currently only has chat_completion.
                # But the provider interface has completion.
                # Let's assume we can access provider or LLMService will be updated.
                # For now, I'll use self.llm_service.provider.completion if available
                
                if hasattr(self.llm_service.provider, 'completion'):
                    response_content, _ = self.llm_service.provider.completion(
                        model=model,
                        prompt=prompt_text,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                else:
                    # Fallback to chat if completion not available?
                    # Or raise error.
                    raise NotImplementedError("Completion not supported by this service/provider")

                if prompt_instance.validate(response_content, prompt=prompt_text):
                    return prompt_instance.clean_up(response_content, prompt=prompt_text)
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        return prompt_instance.get_fail_safe()

    def _execute_new_style_chat(self,
                                prompt_text: str,
                                prompt_instance: BasePrompt,
                                input_data: Any,
                                model: str,
                                temperature: float,
                                max_tokens: Optional[int],
                                max_retries: int,
                                **kwargs) -> Any:
        """Execute a new-style schema-based prompt using chat completion."""
        messages = [{"role": "user", "content": prompt_text}]
        
        for i in range(max_retries + 1):
            try:
                response_content = self.llm_service.chat_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Parse response into output schema
                output = self._parse_new_style_output(response_content, prompt_instance)
                
                # Apply post-processing if available
                if hasattr(prompt_instance, 'post_process') and input_data is not None:
                    if isinstance(input_data, dict):
                        input_obj = prompt_instance.input_schema(**input_data)
                    else:
                        input_obj = input_data
                    output = prompt_instance.post_process(output, input_obj)
                
                return output
                
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        return prompt_instance.get_fail_safe()

    def _execute_new_style_completion(self,
                                      prompt_text: str,
                                      prompt_instance: BasePrompt,
                                      input_data: Any,
                                      model: str,
                                      temperature: float,
                                      max_tokens: Optional[int],
                                      max_retries: int,
                                      **kwargs) -> Any:
        """Execute a new-style schema-based prompt using completion."""
        for i in range(max_retries + 1):
            try:
                if hasattr(self.llm_service.provider, 'completion'):
                    response_content, _ = self.llm_service.provider.completion(
                        model=model,
                        prompt=prompt_text,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                else:
                    # Fallback to chat
                    messages = [{"role": "user", "content": prompt_text}]
                    response_content = self.llm_service.chat_completion(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                
                # Parse response into output schema
                output = self._parse_new_style_output(response_content, prompt_instance)
                
                # Apply post-processing if available
                if hasattr(prompt_instance, 'post_process') and input_data is not None:
                    if isinstance(input_data, dict):
                        input_obj = prompt_instance.input_schema(**input_data)
                    else:
                        input_obj = input_data
                    output = prompt_instance.post_process(output, input_obj)
                
                return output
                
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        return prompt_instance.get_fail_safe()

    def _parse_new_style_output(self, response_content: str, prompt_instance: BasePrompt) -> Any:
        """
        Parse raw LLM response into the output schema.
        
        This handles simple outputs like "8" for WakeUpHourOutput(hour=8),
        and list outputs like daily plan activities.
        """
        response_content = response_content.strip()
        output_schema = prompt_instance.output_schema
        schema_name = output_schema.__name__
        
        # Try to parse as JSON first
        try:
            data = json.loads(response_content)
            return output_schema(**data)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Special handling for TaskDecompOutput - parse numbered list with durations
        if schema_name == 'TaskDecompOutput':
            subtasks = self._parse_task_decomp_list(response_content)
            if subtasks:
                return output_schema(subtasks=subtasks)
        
        # Special handling for NewDecompScheduleOutput - same format as TaskDecompOutput
        if schema_name == 'NewDecompScheduleOutput':
            subtasks = self._parse_task_decomp_list(response_content)
            if subtasks:
                return output_schema(subtasks=subtasks)
        
        # Special handling for triple outputs (subject, predicate, object)
        if schema_name in ('EventTripleOutput', 'ActObjEventTripleOutput'):
            triple = self._parse_event_triple(response_content)
            if triple:
                return output_schema(subject=triple[0], predicate=triple[1], object=triple[2])
        
        # For simple single-field outputs, try to extract the value
        schema_fields = output_schema.__fields__
        if len(schema_fields) == 1:
            field_name = list(schema_fields.keys())[0]
            field = schema_fields[field_name]
            field_type = field.outer_type_
            
            # Try to parse based on field type
            # Check for int types (including constrained int from pydantic)
            is_int_type = field_type == int or (isinstance(field_type, type) and issubclass(field_type, int))
            is_float_type = field_type == float or (isinstance(field_type, type) and issubclass(field_type, float) and not issubclass(field_type, int))
            is_str_type = field_type == str or (isinstance(field_type, type) and issubclass(field_type, str))
            
            try:
                if is_int_type:
                    # Handle time formats like "8 AM", "6:00 AM", "8:00am", etc.
                    # First check for AM/PM time format
                    time_match = re.search(r'(\d{1,2})(?::\d{2})?\s*(?:am|AM|a\.m\.)?', response_content)
                    if time_match:
                        hour = int(time_match.group(1))
                        # Convert PM times to 24-hour format if needed
                        if re.search(r'pm|PM|p\.m\.', response_content) and hour < 12:
                            hour += 12
                        elif re.search(r'am|AM|a\.m\.', response_content) and hour == 12:
                            hour = 0
                        return output_schema(**{field_name: hour})
                    # Fallback: Extract first number from response
                    numbers = re.findall(r'\d+', response_content)
                    if numbers:
                        return output_schema(**{field_name: int(numbers[0])})
                elif is_str_type:
                    # For location outputs (sector, arena, game_object), extract clean location name
                    if field_name in ('sector', 'arena', 'game_object'):
                        clean_value = self._extract_location_name(response_content, field_name)
                        return output_schema(**{field_name: clean_value})
                    return output_schema(**{field_name: response_content})
                elif is_float_type:
                    numbers = re.findall(r'[\d.]+', response_content)
                    if numbers:
                        return output_schema(**{field_name: float(numbers[0])})
                # Handle List[str] - common for activities, keywords, etc.
                elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                    # Parse numbered list like "2) eat breakfast, 3) go to work..."
                    items = self._parse_numbered_list(response_content)
                    if items:
                        return output_schema(**{field_name: items})
            except Exception as parse_ex:
                logger.debug(f"Parse attempt failed for field type {field_type}: {parse_ex}")
                pass
            
            # Fallback: For str fields, try to use the raw response
            if not is_int_type and not is_float_type:
                try:
                    return output_schema(**{field_name: response_content})
                except Exception:
                    pass
        
        # Last resort: try to construct output with the raw response as-is for any single field
        if len(schema_fields) == 1:
            field_name = list(schema_fields.keys())[0]
            try:
                return output_schema(**{field_name: response_content})
            except Exception:
                pass
        
        # If all parsing fails, raise an error (will trigger retry or fail_safe)
        raise ValueError(f"Could not parse response '{response_content}' into {output_schema.__name__}")

    def _extract_location_name(self, response: str, field_name: str) -> str:
        """
        Extract a clean location name from LLM response.
        Handles responses like "Placeholder should go to a bedroom." -> "bedroom"
        or "The hobbs cafe" -> "hobbs cafe"
        """
        response = response.strip()
        
        # Remove common prefixes like "X should go to", "X could go to", etc.
        patterns = [
            r'^.*?should go to\s+(?:the\s+)?(.+?)\.?$',
            r'^.*?could go to\s+(?:the\s+)?(.+?)\.?$',
            r'^.*?go to\s+(?:the\s+)?(.+?)\.?$',
            r'^.*?would be\s+(?:the\s+)?(.+?)\.?$',
            r'^(?:the\s+)?(.+?)\.?$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, response, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                # Remove trailing period if present
                if result.endswith('.'):
                    result = result[:-1].strip()
                # Remove leading "a " or "an "
                result = re.sub(r'^(?:a|an)\s+', '', result, flags=re.IGNORECASE)
                if result:
                    return result
        
        return response

    def _parse_task_decomp_list(self, text: str) -> List[Any]:
        """
        Parse a task decomposition response like:
        "1) Kelly is doing X. (duration in minutes: 15, minutes left: 165)"
        Returns a list of SubTask objects.
        """
        from persona.prompt_template.schemas.planning import SubTask
        
        subtasks = []
        # Split by numbered items first
        lines = re.split(r'(?=\d+\))', text)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Pattern to match: number) description (duration in minutes: X, ...)
            match = re.match(r'\d+\)\s*(.+?)\s*\(duration in minutes:\s*(\d+)', line, re.DOTALL)
            if match:
                desc = match.group(1).strip()
                duration = match.group(2)
                # Remove "Name is " prefix if present
                desc = re.sub(r'^[A-Za-z]+\s+is\s+', '', desc)
                # Clean up the description
                if desc.endswith('.'):
                    desc = desc[:-1].strip()
                if desc:
                    try:
                        subtasks.append(SubTask(description=desc, duration_minutes=int(duration)))
                    except Exception:
                        pass
        
        return subtasks

    def _parse_numbered_list(self, text: str) -> List[str]:
        """
        Parse a numbered list response like "2) eat breakfast, 3) go to work..."
        Returns a list of items.
        """
        items = []
        # Split by number followed by ) 
        parts = re.split(r'\d+\)', text)
        for part in parts:
            part = part.strip()
            if part:
                # Remove trailing punctuation and clean up
                if part.endswith(','):
                    part = part[:-1].strip()
                if part.endswith('.'):
                    part = part[:-1].strip()
                if part:
                    items.append(part)
        return items

    def _parse_event_triple(self, text: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse an event triple from LLM response like "(kitchen sink, is, being used)".
        Returns a tuple of (subject, predicate, object) or None if parsing fails.
        """
        text = text.strip()
        
        # Try to match tuple format: (subject, predicate, object)
        # Handle both with and without parentheses
        match = re.match(r'\(?\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^)]+?)\s*\)?$', text)
        if match:
            subject = match.group(1).strip()
            predicate = match.group(2).strip()
            obj = match.group(3).strip()
            return (subject, predicate, obj)
        
        # Try alternative format without parentheses: subject, predicate, object
        parts = text.split(',')
        if len(parts) >= 3:
            subject = parts[0].strip()
            predicate = parts[1].strip()
            # Join remaining parts as object (in case object has commas)
            obj = ','.join(parts[2:]).strip()
            # Remove surrounding parentheses if present
            if subject.startswith('('):
                subject = subject[1:].strip()
            if obj.endswith(')'):
                obj = obj[:-1].strip()
            return (subject, predicate, obj)
        
        return None
