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

def extract_current_discussion_course(chat_history):
    """Extract the specific course currently being discussed"""
    current_course = None
    
    # Look through recent messages to find what course is being discussed
    recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
    
    for message in reversed(recent_messages):  # Start from most recent
        content = message.get("content", "").lower()
        
        # Look for course-specific mentions
        if "b.des in animation" in content or "animation and visual effects" in content:
            current_course = "B.Des in Animation and Visual Effects"
            break
        elif "computer science" in content and "engineering" in content:
            current_course = "Computer Science and Engineering"
            break
        elif "bachelor of technology" in content and "information science" in content:
            current_course = "Bachelor of Technology in Information Science"
            break
        elif "b.com" in content or "commerce" in content:
            current_course = "Bachelor of Commerce"
            break
        # Add more course patterns as needed
    
    return current_course

def check_if_asking_about_specific_course(user_message, chat_history):
    """Check if user is asking about a specific course mentioned in recent conversation"""
    if not user_message:
        return None
    
    message_lower = user_message.lower()
    
    # First check if they're asking about a specific course in this message
    if "animation" in message_lower and ("b.des" in message_lower or "visual effects" in message_lower):
        return "B.Des in Animation and Visual Effects"
    
    # If not, check what course is currently being discussed
    current_course = extract_current_discussion_course(chat_history)
    
    # If asking follow-up questions about career/jobs/details, assume it's about current course
    followup_keywords = [
        "job opportunities", "career prospects", "employment", "salary", "placement",
        "subjects", "curriculum", "syllabus", "details", "more about", "tell me about",
        "how is", "what about", "opportunities", "scope", "future"
    ]
    
    if any(keyword in message_lower for keyword in followup_keywords) and current_course:
        return current_course
    
    return None
def extract_initial_recommended_courses(chat_history):
    """Extract the courses that were initially recommended to the student"""
    initial_courses = "The courses initially recommended to you"
    
    # Find the first assistant message (initial recommendation)
    for message in chat_history:
        if message.get("role") == "assistant":
            content = message.get("content", "")
            # Extract course names that were mentioned in the initial recommendation
            if content and len(content) > 100:  # Substantial response likely containing recommendations
                initial_courses = f"Here's what I initially recommended to you:\n\n{content[:800]}..."
                break
    
    return initial_courses

def check_if_asking_for_alternatives(user_message):
    """Check if the student is specifically asking for different/alternative courses"""
    if not user_message:
        return False
    
    message_lower = user_message.lower()
    
    # Keywords that indicate they want different options
    alternative_keywords = [
        "other options", "different courses", "alternatives", "other courses",
        "something else", "different options", "more options", "other programs",
        "different field", "change", "instead", "rather than", "not interested",
        "don't like", "different area", "explore other", "what else",
        "any other", "show me other", "different degree", "other majors"
    ]
    
    # Check if any alternative keywords are present
    for keyword in alternative_keywords:
        if keyword in message_lower:
            return True
    
    return False
def filter_and_match_courses(courses, profile):
    """Filter courses by degree level and match to profile with MEDIUM weight for activities"""
    degree_level = profile.get("degree_level", "Bachelor's Degree")
    interests = profile.get("interests", [])
    activities = profile.get("activities", [])  # Medium weightage
    derived_skills = profile.get("derived_skills", [])  # Medium weightage
    
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
    
    # Enhanced matching with MEDIUM weight for activities
    if interests or activities:
        highly_matched_courses = []  # Strong matches (interests + activities)
        moderately_matched_courses = []  # Medium matches (interests OR activities)
        unmatched_courses = []  # No matches
        
        for course in filtered_courses:
            course_text = (course.get('course', '') + ' ' + course.get('degree', '')).lower()
            
            interest_match = False
            activity_match = False
            
            # Check interest matching
            for interest in interests:
                interest_lower = interest.lower()
                if interest_lower in course_text or any(word in course_text for word in interest_lower.split()):
                    interest_match = True
                    break
            
            # Check activity matching - MEDIUM WEIGHTAGE
            activity_course_mapping = {
                "leadership": ["management", "business", "administration", "leadership"],
                "technical projects": ["computer", "technology", "engineering", "software"],
                "creative arts": ["design", "art", "creative", "visual", "communication"],
                "sports": ["sports", "physical education", "athletics", "fitness"],
                "community service": ["social work", "psychology", "counseling", "humanities"],
                "academic excellence": ["research", "science", "mathematics", "academic"],
                "performance": ["music", "performing arts", "media", "communication"],
                "business": ["business", "commerce", "management", "finance", "entrepreneurship"]
            }
            
            for activity in activities:
                activity_lower = activity.lower()
                for activity_type, course_keywords in activity_course_mapping.items():
                    if activity_type in activity_lower:
                        if any(keyword in course_text for keyword in course_keywords):
                            activity_match = True
                            break
                if activity_match:
                    break
            
            # Prioritize based on both interest and activity matches
            if interest_match and activity_match:
                highly_matched_courses.append(course)  # Best match
            elif interest_match or activity_match:
                moderately_matched_courses.append(course)  # Good match
            else:
                unmatched_courses.append(course)  # Include but lower priority
        
        # Return in priority order: highly matched → moderately matched → unmatched
        return highly_matched_courses + moderately_matched_courses + unmatched_courses
    
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
1. Analyze the student's strengths (top academic subjects), interests, AND extracurricular activities
2. Give MEDIUM WEIGHT to their activities and derived skills when making recommendations
3. Suggest 3-4 best-fit {degree_level} courses that align with their complete profile
4. For each recommended course, explain WHY it's a good fit using second person (you/your)
5. Include the course URL for each recommendation
6. Mention how their activities and derived skills make them suitable for each course

IMPORTANT: 
- Consider activities as EQUALLY important as academic interests when recommending courses
- If they have leadership activities, mention management/business potential
- If they have technical projects, highlight engineering/technology fit
- If they have creative activities, emphasize design/arts alignment
- If they have sports activities, consider sports science/physical education
- Only recommend {degree_level} courses - do not mix bachelor's and master's programs
- Always address the student directly using "you" and "your" throughout your response
- Keep the heading text size normal (not overly large)

Format your response in a friendly, supportive tone. Structure it with clear headings and include the URLs so students can learn more about each course.

End by asking: "Would you like me to explain more about any of these courses, or would you prefer to explore other options?"
"""

    return prompt

def prepare_context_prompt(profile, courses, chat_history):
    """Prepare prompt with full chat context - focused on initial recommendations"""
    profile_str = json.dumps(profile, indent=2)
    
    # Get the initial recommended courses from the first assistant message
    initial_courses = extract_initial_recommended_courses(chat_history)
    degree_level = profile.get("degree_level", "Bachelor's Degree")
    
    # Build conversation history - only include the last few relevant messages
    recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
    conversation_context = ""
    
    # Only include user messages for context, not the assistant responses to avoid echoing
    user_messages = [msg for msg in recent_messages if msg.get("role") == "user"]
    if user_messages:
        latest_user_message = user_messages[-1].get("content", "")
        conversation_context = f"Student's current question: {latest_user_message}"
    
    # Check if student is asking for different/alternative courses
    asking_for_alternatives = check_if_asking_for_alternatives(latest_user_message if user_messages else "")
    
    # Check if student is asking about a specific course
    specific_course = check_if_asking_about_specific_course(latest_user_message if user_messages else "", chat_history)

    if asking_for_alternatives:
        # Only then provide new course options
        relevant_courses = filter_and_match_courses(courses, profile)
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

        prompt = f"""
You are an expert academic advisor at Jain University helping a student choose the right course.

Student Profile:
{profile_str}

The student is asking for different/alternative course options from what was initially suggested.

Available {degree_level} Courses:
{course_catalog}

{conversation_context}

Instructions:
- The student wants to explore different options, so you can suggest new courses
- Only recommend {degree_level} courses
- Provide helpful, specific advice about these alternative courses
- Include course URLs when recommending specific programs
- Be supportive and encouraging
- IMPORTANT: Always address the student directly using "you" and "your"
- Format recommendations clearly with explanations

Respond naturally as their personal academic advisor offering alternative options.
"""
    elif specific_course:
        # Student is asking about a specific course - focus only on that course
        prompt = f"""
You are an expert academic advisor at Jain University helping a student choose the right course.

Student Profile:
{profile_str}

IMPORTANT: The student is currently asking about **{specific_course}** specifically. 

{conversation_context}

Instructions:
- Answer ONLY about {specific_course} - do NOT mention other courses
- If they ask about job opportunities, career prospects, subjects, etc. - relate everything to {specific_course}
- Provide detailed, helpful information specifically about {specific_course}
- Do NOT suggest other courses or alternatives unless they specifically ask
- Be informative and enthusiastic about {specific_course}
- IMPORTANT: Always address the student directly using "you" and "your"
- Keep your response focused entirely on {specific_course}

Your goal is to provide comprehensive information about {specific_course} that the student is asking about.

Respond naturally as their personal academic advisor, focusing exclusively on {specific_course}.
"""
    else:
        # Focus on initially recommended courses only
        prompt = f"""
You are an expert academic advisor at Jain University helping a student choose the right course.

Student Profile:
{profile_str}

IMPORTANT CONTEXT: You have already suggested specific courses to this student in your initial recommendation. Here are the courses you initially recommended:
{initial_courses}

{conversation_context}

Instructions:
- FOCUS ONLY on the courses you initially recommended - do NOT suggest new courses
- Answer the student's question in the context of those initially recommended courses
- If they ask about career prospects, job opportunities, curriculum, etc. - relate it to the initially suggested courses
- If they ask general questions, tie your answers back to how the initially recommended courses address their needs
- Do NOT offer alternative courses or new suggestions unless they specifically ask for different options
- Be helpful and informative about the courses you already suggested
- IMPORTANT: Always address the student directly using "you" and "your"
- Keep your response focused and conversational

Your goal is to help the student understand and feel confident about the courses you initially recommended, not to overwhelm them with more options.

Respond naturally as their personal academic advisor, staying focused on the initially suggested courses.
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