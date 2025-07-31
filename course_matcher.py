import json
import os
import openai
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
openai.api_key = os.getenv("MISTRAL_API_KEY")

# Set Mistral endpoint (official API)
openai.api_base = "https://api.mistral.ai/v1"

def load_courses(path="courses.json"):
    with open(path, "r") as f:
        return json.load(f)

def prepare_prompt(profile, courses):
    profile_str = json.dumps(profile, indent=2)
    course_catalog = "\n".join(
        [f"- [{c['degree']} > {c['course']}]({c['source_url']}) (Subjects: {', '.join(c.get('subjects', []))})"
     for c in courses]
    )


    prompt = f"""
You are an academic advisor helping students choose the right university course.

Here is the student's profile:
{profile_str}

Here is the course catalog:
{course_catalog}

Your task:
1. Suggest 3 best-fit courses based on the student's strengths, favorite subject (highest priority), interests, and aspirations.
2. Explain WHY these 3 courses fit well.
3. Infer what skills the student has and map them to each course.

Respond in a friendly, supportive tone, like you're talking to the student.
End by asking: “Do you want to explore these courses or do you want me to suggest more options for you?”
"""

    return prompt

def get_recommendation(profile, courses):
    prompt = prepare_prompt(profile, courses)
    
    response = openai.ChatCompletion.create(
        model="mistral-tiny",  # or "mistral-medium" / "mistral-small" depending on your plan
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700
    )
    
    return response["choices"][0]["message"]["content"]
