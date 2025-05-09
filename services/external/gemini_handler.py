# services/external/gemini_handler.py
# --- Use Imports based on User's V1/Preference ---
from google import genai
from google.genai import types # Import types for GenerateContentConfig
# --- End Imports ---

from core.config import settings
from typing import List, Dict, Optional
import logging
import re
import json

logger = logging.getLogger(__name__)

# --- Gemini Client Initialization (User manages errors/validation) ---
# Using the genai.Client pattern EXACTLY as requested by the user
client: Optional[genai.Client] = None
try:
    # Initialize using the Client class from 'google.genai'
    client = genai.Client(api_key=settings.gemini_api_key) # Or just genai.Client() if key is implicit
    logger.info("genai.Client object initialized via V1 pattern.")
    # Verify if client.aio exists, log warning if not
    if client and not hasattr(client, 'aio'):
         logger.warning("Initialized genai.Client does not seem to have the '.aio' attribute for async operations. Async calls might fail.")

except AttributeError as ae:
    logger.error(f"AttributeError initializing genai.Client: {ae}. 'Client' class might not exist in 'google.genai' or API key handling differs.", exc_info=True)
    client = None # Ensure client is None if init fails
except Exception as e:
    logger.error(f"Failed to initialize genai.Client: {e}", exc_info=True)
    client = None

# Define model name (use the one from user's V1/example)
# Ensure this model name is compatible with the Client API version you are using
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Or "gemini-2.0-flash" / "gemini-pro" etc.

# --- System Prompts ---
SYSTEM_PROMPT_EMOTION_BREAKDOWN = """
Analyze the provided journal entries. Identify the 3 to 5 most dominant emotions expressed.
Output the result as a comma-separated list of key-value pairs, where the key is the emotion (adjective) and the value is its estimated percentage (integer).
Example format: "Happy-30,Excited-23,Disappoint-12,Curiosity-20,Calm-15"
Another example: "Sad-30,Self Criticizing-45,Demotivated-25"
Ensure the percentages roughly reflect the emotional weight across all entries provided.
The total percentage does not necessarily need to sum to 100. Focus on the relative prominence.
"""

SYSTEM_PROMPT_REFLECTION = """
You are a compassionate and insightful mental wellness companion. A user has just written a short journal entry (1 to 10 sentences). Your task is to provide a reflection that mirrors their emotion, offers gentle insight, or encouragement— something they may not have consciously realized. The reflection should feel like it comes from someone deeply attuned to their feelings and subconscious mind.
Your response is recommended to be around 3 sentences.
Speak with warmth, wisdom, and clarity.
Avoid repeating what the user wrote— respond to it, not with it.
Focus on emotion, patterns, or deeper truths beneath the surface.
Never offer solutions or advice— only insight, reflection, or emotional resonance.
This is not a summary. It is not a reply. It is a mirror

Here are two example outputs for an idea of what is a good output
1. “You’ve been holding it together — and that counts. Today was hard, but you still showed up.”
2. “It's good you apologized. Acknowledge your stress, find healthy ways to release it, and rebuild trust with your friend through consistent actions.”
"""
# --- End System Prompts ---


async def generate_emotion_breakdown_async(journal_prompts: List[str]) -> Optional[Dict[str, float]]:
    """
    Analyzes prompts using client.aio.models.generate_content (V1 style - async)
    to generate an emotional breakdown.

    Args:
        journal_prompts: A list of journal entry texts.

    Returns:
        A dictionary mapping emotion names to percentages, or None on failure.

    Raises:
        RuntimeError: If the 'client' object is None or lacks the 'aio' attribute.
    """
    if client is None or not hasattr(client, 'aio'):
        logger.error("Gemini client (genai.Client) or its 'aio' attribute is not available for emotion breakdown.")
        raise RuntimeError("Gemini client or its async interface failed to initialize.")

    if not journal_prompts:
        logger.warning("generate_emotion_breakdown_async called with no prompts.")
        return None

    combined_prompts = "\n---\n".join(journal_prompts)
    full_prompt = f"Analyze the following journal entries:\n\n{combined_prompts}"
    logger.info(f"Requesting emotion breakdown via client.aio.models.generate_content for {len(journal_prompts)} prompts...")

    try:
        # --- Correct V1 Style Async Call using client.aio ---
        config = types.GenerateContentConfig(
             # Pass generation parameters here if needed
        )
        # Use client.aio for the async version of client.models.generate_content
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME, # Pass model name directly if required by this method
            contents=[full_prompt],
            generation_config=config
            # System prompt might need to be handled differently for client API
            # Check if config or generate_content accepts system_instruction
        )
        # --- End Call ---

        # --- Parsing Logic (remains the same) ---
        if response and hasattr(response, 'text') and response.text:
            logger.debug(f"Gemini raw response for emotion breakdown: {response.text}")
            pattern = re.compile(r"([a-zA-Z\s]+)\s*-\s*(\d+(?:\.\d+)?)")
            matches = pattern.findall(response.text)
            if not matches:
                 logger.warning(f"Could not parse Gemini emotion breakdown response: '{response.text}'")
                 return None
            emotions_dict = {}
            for name, percent_str in matches:
                try:
                    emotion_name = name.strip()
                    percentage = float(percent_str)
                    if 0 <= percentage <= 100:
                         emotions_dict[emotion_name] = percentage
                    else:
                         logger.warning(f"Parsed percentage {percentage} for emotion '{emotion_name}' is outside valid range (0-100). Skipping.")
                except ValueError:
                    logger.warning(f"Could not convert percentage '{percent_str}' to float for emotion '{name}'. Skipping.")
                    continue
            if not emotions_dict:
                 logger.warning("Parsing Gemini response yielded no valid emotion-percentage pairs.")
                 return None
            logger.info(f"Successfully parsed emotions: {emotions_dict}")
            return emotions_dict
        else:
            logger.error(f"Received empty or invalid response from Gemini for emotion breakdown.")
            return None
        # --- End Parsing Logic ---

    except AttributeError as ae:
         logger.error(f"AttributeError during client.aio.models.generate_content call: {ae}. Verify method existence and parameters.", exc_info=True)
         raise RuntimeError(f"Gemini API async call failed: {ae}")
    except Exception as e:
        logger.error(f"Error during Gemini API call for emotion breakdown: {e}", exc_info=True)
        return None


async def generate_single_reflection_async(prompt: str, emotions: int) -> Optional[str]:
    """
    Generates a single reflection using client.aio.models.generate_content (V1 style - async).

    Args:
        prompt: The user's journal text.
        emotions: The user's emotion score.

    Returns:
        The generated reflection text as a string, or None if generation fails.

    Raises:
        RuntimeError: If the 'client' object is None or lacks the 'aio' attribute.
    """
    if client is None or not hasattr(client, 'aio'):
        logger.error("Gemini client (genai.Client) or its 'aio' attribute is not available for single reflection.")
        raise RuntimeError("Gemini client or its async interface failed to initialize.")

    logger.info(f"Requesting single reflection via client.aio.models.generate_content for prompt (len: {len(prompt)}), emotions: {emotions}")
    content_for_gemini = [prompt, f"emotions,{emotions}"]

    try:
        # --- Correct V1 Style Async Call using client.aio ---
        # Pass system prompt via GenerateContentConfig, like V1
        config = types.GenerateContentConfig(
             # Add generation parameters if needed
             system_instruction=SYSTEM_PROMPT_REFLECTION # Pass system prompt via config
        )

        # Use client.aio for the async version
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=content_for_gemini,
            generation_config=config
        )
        # --- End Call ---

        # --- Response Handling (remains the same) ---
        if response and hasattr(response, 'text') and response.text:
            logger.info("Successfully generated single reflection.")
            reflection_text = response.text.strip().strip('"')
            return reflection_text
        else:
            logger.error("Received empty or invalid response from Gemini for single reflection.")
            return None
        # --- End Response Handling ---

    except AttributeError as ae:
         logger.error(f"AttributeError during client.aio.models.generate_content call: {ae}. Verify method existence and parameters.", exc_info=True)
         raise RuntimeError(f"Gemini API async call failed: {ae}")
    except Exception as e:
        logger.error(f"Error during Gemini API call for single reflection: {e}", exc_info=True)
        return None

# --- Placeholder for other functions (e.g., YSYM) using client.aio pattern ---
# async def generate_full_reflection_with_ysym_async(prompt: str, emotions: int) -> Dict:
#    if client is None or not hasattr(client, 'aio'): raise RuntimeError("Gemini client error.")
#    # Replicate V1's two calls using await client.aio.models.generate_content(...)
#    pass
# --- End Placeholder ---