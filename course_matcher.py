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

def filter_and_match_courses(courses, profile):
    """Filter courses by degree level and match to profile - no bias"""
    degree_level = profile.get("degree_level", "Bachelor's Degree")
    interests = profile.get("interests", [])
    
    # First filter by degree level
    filtered_courses = []
    for course in courses:
        course_name = course.get('course', '').lower()
        
        if degree_level == "Bachelor's Degree":
            bachelor_keywords = ['bachelor', 'b.com', 'b.sc', 'b.tech', 'b.des', 'b.p.ed', 'undergraduate']
            if any(keyword in course_name for keyword in bachelor_keywords):
                filtered_courses.append(course)
        
        elif degree_level == "Master's Degree":
            master_keywords = ['master', 'm.com', 'm.sc', 'm.tech', 'm.des', 'm.p.ed', 'postgraduate']
            if any(keyword in course_name for keyword in master_keywords):
                filtered_courses.append(course)
    
    # Simple interest matching - no special weights or bias
    if interests:
        matched_courses = []
        unmatched_courses = []
        
        for course in filtered_courses:
            course_text = (course.get('course', '') + ' ' + course.get('degree', '')).lower()
            
            # Check if course relates to any student interest
            course_matches_interest = False
            for interest in interests:
                interest_lower = interest.lower()
                
                # Simple keyword matching - all interests treated equally
                if interest_lower in course_text or any(word in course_text for word in interest_lower.split()):
                    course_matches_interest = True
                    break
            
            if course_matches_interest:
                matched_courses.append(course)
            else:
                unmatched_courses.append(course)
        
        # Return matched courses first, then others (but don't exclude anything)
        return matched_courses + unmatched_courses
    
    return filtered_courses

def prepare_initial_prompt(profile, courses):
    """Prepare the initial recommendation prompt"""
    profile_str = json.dumps(profile, indent=2)
    
    # Filter and match courses without bias
    relevant_courses = filter_and_match_courses(courses, profile)
    degree_level = profile.get("degree_level", "Bachelor's Degree")
    
    # Create a cleaner course catalog with URLs
    course_catalog = ""
    seen_courses = set()
    
    for c in relevant_courses:
        course_name = c.get('course', '')
        degree_name = c.get('degree', '')
        source_url = c.get('source_url', '')
        
        # Skip duplicates and invalid entries
        if (course_name, degree_name) in seen_courses or len(course_name.split()) < 3:
            continue
            
        seen_courses.add((course_name, degree_name))
        subjects = c.get('subjects', [])
        subjects_str = f" (Subjects: {', '.join(subjects)})" if subjects else ""
        
        course_catalog += f"- **{course_name}** from {degree_name}{subjects_str}\n  URL: {source_url}\n\n"

    # Check if profile needs clarification
    needs_clarification = profile.get("needs_clarification", False)
    clarifying_questions = profile.get("clarifying_questions", [])
    completeness_score = profile.get("completeness_score", 100)

    if needs_clarification and clarifying_questions:
        prompt = f"""
You are an expert academic advisor helping students choose the right university course.

Here is the student's current profile:
{profile_str}

IMPORTANT: The student's profile is only {completeness_score}% complete. Before giving course recommendations, you need to gather more information.

Your task:
1. Acknowledge what information you have about the student
2. Explain that you'd like to understand them better to give more personalized recommendations
3. Ask ONE of these clarifying questions (choose the most important one):
{chr(10).join([f"- {q}" for q in clarifying_questions[:2]])}

4. Be encouraging and explain that this will help you suggest the best-fit courses

Keep your response friendly and conversational. Don't recommend specific courses yet - focus on gathering more information first.
"""
    else:
        prompt = f"""
You are an expert academic advisor helping students choose the right university course.

Here is the student's profile:
{profile_str}

Here are the available {degree_level} courses:
{course_catalog}

Your task:
1. Analyze the student's strengths, interests, favorite subjects, and career aspirations
2. Suggest 3-4 best-fit {degree_level} courses that align with their profile
3. For each recommended course, explain WHY it's a good fit using second person (you/your)
4. Include the course URL for each recommendation
5. Mention specific skills you have that match each course

IMPORTANT: 
- Only recommend {degree_level} courses - do not mix bachelor's and master's programs
- Always address the student directly using "you" and "your" throughout your response
- Keep the heading text size normal (not overly large)

Format your response in a friendly, supportive tone. Structure it with clear headings and include the URLs so students can learn more about each course.

End by asking: "Would you like me to explain more about any of these courses, or would you prefer to explore other options?"
"""

    return prompt

def prepare_context_prompt(profile, courses, chat_history):
    """Prepare prompt with full chat context"""
    profile_str = json.dumps(profile, indent=2)
    
    # Filter and match courses without bias
    relevant_courses = filter_and_match_courses(courses, profile)
    degree_level = profile.get("degree_level", "Bachelor's Degree")
    
    # Create course catalog
    course_catalog = ""
    seen_courses = set()
    
    for c in relevant_courses:
        course_name = c.get('course', '')
        degree_name = c.get('degree', '')
        source_url = c.get('source_url', '')
        
        if (course_name, degree_name) in seen_courses or len(course_name.split()) < 3:
            continue
            
        seen_courses.add((course_name, degree_name))
        subjects = c.get('subjects', [])
        subjects_str = f" (Subjects: {', '.join(subjects)})" if subjects else ""
        
        course_catalog += f"- **{course_name}** from {degree_name}{subjects_str}\n  URL: {source_url}\n\n"

    # Build conversation history - only include the last few relevant messages
    recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
    conversation_context = ""
    
    # Only include user messages for context, not the assistant responses to avoid echoing
    user_messages = [msg for msg in recent_messages if msg.get("role") == "user"]
    if user_messages:
        latest_user_message = user_messages[-1].get("content", "")
        conversation_context = f"Student's current question: {latest_user_message}"

    prompt = f"""
You are an expert academic advisor at Jain University helping a student choose the right course.

Student Profile:
{profile_str}

Available {degree_level} Courses:
{course_catalog}

{conversation_context}

Instructions:
- Answer the student's question directly and naturally
- Only recommend {degree_level} courses - do not mix bachelor's and master's programs
- Provide helpful, specific advice about courses and career paths
- Include course URLs when recommending specific programs
- Be supportive and encouraging
- IMPORTANT: Always address the student directly using "you" and "your"
- Do NOT repeat or echo previous conversation history
- Keep your response focused and conversational
- If recommending courses, format them clearly with explanations

Respond naturally as their personal academic advisor.
"""

    return prompt

def get_recommendation_with_context(profile, courses, chat_history):
    """Get recommendation with full chat context"""
    if not chat_history:
        # Initial recommendation
        prompt = prepare_initial_prompt(profile, courses)
    else:
        # Contextual response
        prompt = prepare_context_prompt(profile, courses, chat_history)
    
    try:
        response = openai.ChatCompletion.create(
            model="mistral-tiny",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        return response["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"I apologize, but I'm having trouble connecting to generate recommendations right now. Error: {str(e)}. Please try again in a moment."

def get_recommendation(profile, courses):
    """Legacy function for backward compatibility"""
    return get_recommendation_with_context(profile, courses, [])