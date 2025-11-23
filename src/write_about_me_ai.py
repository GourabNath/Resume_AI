__version__ = "0.4.0"

# Writing this function in GitHub 

__version__ = "0.4.0"

import os
from IPython.display import Markdown, display
from openai import OpenAI
import openai
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

def write_about_me(details, about_me_rules, feedback_history=None, model = "gpt-4.1-nano"):
    """
    Description: This function helps an user to re-write the about me section of a resume based on the user details and a set of pre-defined rules.
                 This version (v2) also uses the last three validation results as memory to improve the results.

    Arg:
    details (str): details of users-entered about me in the raw text form.
    about_me_rules (str): a set of rules to be provided to the LLM as a guideline to write teh about me. Default is None.
    feedback_history (list): a list containing the previous feedbacks on the generated outputs.
    model = the LLM model to be used

    Out:
    Returns output in JSON (field names: about, highlights, sources, tokens, tone, confidence)
    """

    # Keep only the last 3 feedback entries (if any)
    if feedback_history:
        feedback_history_to_use = feedback_history[-3:]
    else:
        feedback_history_to_use = []

    # Convert to JSON string (pretty format) only if non-empty
    feedback_history_str = json.dumps(feedback_history_to_use, indent=2) if feedback_history_to_use else ""

    #Create your prompts
    system_prompt = f"""You are a professional resume builder who specifically helps to write the 'about me' section of a resume. Here's what you are expected to do:
                    1. Write a very enthusiastic version of about that is expected to attract recruiter's attention
                    2. Keep it short and crisp - energetic and thrilling (6-8 lines)
                    3. Do not make it very generic
                    4. Pick specific details from the user input and personalize your write-up and make it user-specific
                    Return the output **strictly in JSON** using this format:
                          {{
                            "about": "...",
                            "highlights": ["...", "..."],
                            "tokens": <int>,
                            "tone": "energetic",
                            "sources": ["...","..."],
                            "confidence": <float between 0 and 1>
                          }}

                    Additionally, use the linkedIN about me rules of do's and dont's to polish it further:
                    {about_me_rules}

                    Examples:
                    {examples}

                    Here are feedback of your previous work:
                    {feedback_history_str}
                    You should be able to learn from the feedback and improve your response.
                    """

    user_prompt = details

    #Create your message list
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


    #Call OpenAI
    response = openai.chat.completions.create(model=model, messages=messages, temperature=0.4)

    #return the results
    content = response.choices[0].message.content

    #Parse JSON safely
    try:
        data = json.loads(content)
    except:
        data = {"about": content, "highlights": [], "confidence": 0.5}

    return data



def validate_about_me(about_me_generated_json, about_me_original, about_me_rules=None, model="gpt-4.1-nano"):   #without memory
      """
      Description: This function is used to validate the performance of the about me generator by comparing it with a set of pre-defined rules.
                   This version (v2) contains modified system prompt to improve the scoring criteria.

      Args:
      about_me_generated_json (JSON): JSON with field names (about, highlights, sources, tokens, tone, confidence).
      about_me_original (str): details of users-entered about me in the raw text form.
      about_me_rules (str): a set of rules to be provided to the LLM as a guideline to write teh about me. Default is None.
      model = the LLM model to be used

      Out:
      Returns output in JSON for the following format:
                      {{
                        "decision": "go" or "no-go",
                        "score": <float 0..1>,
                        "reasons": ["..."],
                        "checks": {{
                          "length_ok": true/false,
                          "uses_specifics": true/false,
                          "no_hallucination": true/false
                        }}

      """

      system_prompt = f"""
                        You are a resume-quality validator. You will receive:
                        1) the generated about-me JSON (field names: about, highlights, sources, tokens, tone, confidence)
                        2) the original user details used to generate the about-me.

                        Tasks:
                        - Verify factual consistency: every item in highlights/sources must be supported by original details or marked as hallucination.
                        - Verify length: about should be 6-10 lines (tolerate ±2).
                        - Verify tone and specificity (energetic, not generic).
                        - Produce a strict JSON response ONLY in this format:
                              {{
                              "decision": "go" or "no-go",
                              "score": <float 0..1>,
                              "reasons": ["..."],
                              "checks": {{
                                "length_ok": true/false,
                                "uses_specifics": true/false,
                                "no_hallucination": true/false
                              }}

                        - Be a sensitive evaluater and your score SHOULDN'T biased numbers like 0.55, 0.65, etc.
                        - TRY TO KEEP THE SCORES AS FLOATING NUMBERS BETWEEN 0 AND 1. (NEED NOT BE IN THE MULTIPLE OF 5 OR 10)
                        - Here is your SCORING WEIGHTS:
                                length = 20%  (should be short and crisp)
                                tone = 20% (should be energetic, vibrant, and not generic)
                                informative = 40% (should contains many specific information about the person and its experience; generic output = low score, specific output = high score)
                                overall construction = 20% (professionally build paragraph = high score, scattered = low score)



                    Make sure the generated texts are bounded by the following rules:
                    {about_me_rules}

                    Here is an example of (input, output) pair:
                    {examples}
              """

      messages = [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": json.dumps({
              "generated": about_me_generated_json,
              "original_details": about_me_original
          })}
      ]

      resp = openai.chat.completions.create(model=model, messages=messages, temperature=0.0, max_tokens=400)
      content = resp.choices[0].message.content

      try:
          result = json.loads(content)
      except Exception:
          # fallback conservative answer
          result = {
              "decision": "no-go",
              "score": 0.0,
              "reasons": ["validator failed to parse model output"],
              "checks": {"length_ok": False, "uses_specifics": False, "no_hallucination": False},
          }
      return result



if __name__ == '__main__':
    about_me_rules = None
    details = "I am a computer science engineer currently doing a certification on data science"
    print('v', __version__, write_about_me(details, about_me_rules))

    examples=None
    generated_about_me_json = write_about_me(details, about_me_rules)
    about_me_original = details
    print('v', __version__, validate_about_me(generated_about_me_json, about_me_original))

