# services/external/gemini_handler.py
from google import genai
from google.genai import types # Correct import if needed for config
from core.config import settings # Import settings to get API key
from typing import List, Dict, Optional
import logging
import re # Import regex for parsing

logger = logging.getLogger(__name__)

# --- Gemini Client Initialization ---
# Configure the client once when the module loads or via lifespan event
try:
    genai.configure(api_key=settings.gemini_api_key)
    logger.info("Gemini API configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)
    # Handle configuration error appropriately

# Define model name (consider making this configurable via settings)
GEMINI_MODEL_NAME = "gemini-1.5-flash" # Or "gemini-pro", check available models

# --- System Prompts (Based on V1) ---
SYSTEM_PROMPT_EMOTION_BREAKDOWN = """
Analyze the provided journal entries. Identify the 3 to 5 most dominant emotions expressed.
Output the result as a comma-separated list of key-value pairs, where the key is the emotion (adjective) and the value is its estimated percentage (integer).
Example format: "Happy-30,Excited-23,Disappoint-12,Curiosity-20,Calm-15"
Another example: "Sad-30,Self Criticizing-45,Demotivated-25"
Ensure the percentages roughly reflect the emotional weight across all entries provided.
The total percentage does not necessarily need to sum to 100. Focus on the relative prominence.
"""
# Add other system prompts (reflection, ysym, weekly) here later...

# --- End System Prompts ---


async def generate_emotion_breakdown_async(journal_prompts: List[str]) -> Optional[Dict[str, float]]:
    """
    Analyzes journal prompts using Gemini to generate an emotional breakdown.

    Args:
        journal_prompts: A list of journal entry texts.

    Returns:
        A dictionary mapping emotion names to percentages (e.g., {"Happy": 30.0}),
        or None if generation fails or parsing fails.
    """
    if not journal_prompts:
        logger.warning("generate_emotion_breakdown_async called with no prompts.")
        return None

    # Combine prompts into a single string for Gemini analysis
    combined_prompts = "\n---\n".join(journal_prompts)
    full_prompt = f"Analyze the following journal entries:\n\n{combined_prompts}"

    logger.info(f"Requesting emotion breakdown from Gemini for {len(journal_prompts)} prompts...")

    try:
        # Initialize the model (consider doing this once if reusable)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=SYSTEM_PROMPT_EMOTION_BREAKDOWN
            # Add generation_config, safety_settings if needed
        )

        # Use generate_content_async for non-blocking call
        response = await model.generate_content_async(
            contents=[full_prompt] # Pass the combined prompt
            # generation_config=GenerationConfig(...) # Optional config
        )

        # --- Robust Parsing ---
        if response and hasattr(response, 'text') and response.text:
            logger.debug(f"Gemini raw response for emotion breakdown: {response.text}")
            # Use regex to find "Emotion-Percentage" pairs more robustly
            # Allows for spaces around hyphen/comma, case-insensitivity (if needed)
            pattern = re.compile(r"([a-zA-Z\s]+)\s*-\s*(\d+(?:\.\d+)?)") # Emotion-Percentage(float/int)
            matches = pattern.findall(response.text)

            if not matches:
                 logger.warning(f"Could not parse Gemini emotion breakdown response: '{response.text}'")
                 return None

            emotions_dict = {}
            for name, percent_str in matches:
                try:
                    # Strip leading/trailing whitespace from emotion name
                    emotion_name = name.strip()
                    # Convert percentage to float
                    percentage = float(percent_str)
                    # Optional: Validate percentage range (0-100)
                    if 0 <= percentage <= 100:
                         emotions_dict[emotion_name] = percentage
                    else:
                         logger.warning(f"Parsed percentage {percentage} for emotion '{emotion_name}' is outside valid range (0-100). Skipping.")
                except ValueError:
                    logger.warning(f"Could not convert percentage '{percent_str}' to float for emotion '{name}'. Skipping.")
                    continue # Skip this pair if conversion fails

            if not emotions_dict:
                 logger.warning("Parsing Gemini response yielded no valid emotion-percentage pairs.")
                 return None

            logger.info(f"Successfully parsed emotions: {emotions_dict}")
            return emotions_dict
        else:
            logger.error(f"Received empty or invalid response from Gemini for emotion breakdown.")
            # Log response details if possible for debugging
            # logger.error(f"Full Gemini Response: {response}")
            return None

    except Exception as e:
        logger.error(f"Error during Gemini API call for emotion breakdown: {e}", exc_info=True)
        return None # Return None on API error

# Add other async Gemini functions (reflection, weekly, etc.) later