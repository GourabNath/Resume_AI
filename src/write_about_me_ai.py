__version__ = "0.2.1"

import os
from IPython.display import Markdown, display
from openai import OpenAI
import openai
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

def write_about_me(details, about_me_rules=None, model = "gpt-4.1-nano"):
    """
    Description: This function helps an user to re-write the about me section of a resume based on the user details and a set of pre-defined rules.

    Arg:
    details (str): details of users-entered about me in the raw text form.
    about_me_rules (str): a set of rules to be provided to the LLM as a guideline to write teh about me. Default is None.
    model = the LLM model to be used

    Out:
    Returns output in JSON (field names: about, highlights, sources, tokens, tone, confidence)
    """


    system_prompt = f""""You are a professional resume builder who specifically helps to write the 'about me' section of a resume. Here's what you are expected to do:
                    1. Write a very enthusiastic version of about me that is expected to attract recruiter's attention
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
                    """

    #The user prompt is details the user provide for about me
    user_prompt = details

    #The message list
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


    #3. Call OpenAI
    response = openai.chat.completions.create(model=model, messages=messages, temperature=0.6)

    #4. return the results
    content = response.choices[0].message.content

    #5. Parse JSON safely
    try:
        data = json.loads(content)
    except:
        data = {"about": content, "highlights": [], "confidence": 0.5}

    return data



def validate_about_me(about_me_generated_json, about_me_original, model="gpt-4.1-mini"):
      """
      Description: This function is used to validate the performance of the about me generator.

      Args:
      about_me_generated_json (JSON): JSON with field names (about, highlights, sources, tokens, tone, confidence).
      about_me_original (str): details of users-entered about me in the raw text form.
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

      # System prompts
      system_prompt = f"""
                        You are a strict resume-quality validator. You will receive:
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

                        """

      # Messages
      messages = [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": json.dumps({          #json.dumps helps to convert JSON into string
              "generated": about_me_generated_json,
              "original_details": about_me_original
          })}
      ]

      #Call OpenAI API
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
              "suggested_about": ""
          }
      return result

if __name__ == '__main__':
    examples = None
    details = "I am a computer science engineer currently doing a certification on data science"
    print('v', __version__, write_about_me_v1(details))

    generated_about_me_json = write_about_me(details, examples)
    about_me_original = details
    print('v', __version__, validate_about_me(generated_about_me_json, about_me_original))

