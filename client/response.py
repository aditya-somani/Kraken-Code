# This file is created to standardize and structure the way the application handles responses from Large Language Models (LLMs), 
# especially when dealing with both streaming and non-streaming outputs

# Imports
from dataclass import dataclass

# Intuition behind making `StreamEvent`
# When interacting with an LLM, the responses can vary. 
# You might get a full response at once (non-streaming) or chunks of text over time (streaming). 
# Additionally, the response might contain just text, or it might include tool calls, or even an error. 
# StreamEvent acts as a unified schema or class definition for any event that comes from the model. 
# This makes it easier to process and manage different types of responses consistently.

@dataclass
class StreamEvent:
    
