import pdfplumber
import re

def extract_marks_from_pdf(pdf_path):
    marks = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        lines = text.split("\n")
        for line in lines:
            match = re.match(r"(\w+(?: \w+)*):\s*(\d+)%", line)
            if match:
                subject, score = match.groups()
                marks[subject.strip()] = int(score)
    return marks

def extract_interests_from_certificates(cert_paths):
    keywords = {
        "design": "Design",
        "art": "Design",
        "paint": "Design",
        "sports": "Sports",
        "athletics": "Sports",
        "football": "Sports",
        "music": "Music",
        "singing": "Music",
        "tech": "Technology",
        "code": "Technology",
        "programming": "Technology",
    }

    interests = set()

    for path in cert_paths:
        with pdfplumber.open(path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            text = text.lower()
            for kw, label in keywords.items():
                if kw in text:
                    interests.add(label)

    return list(interests)

def build_student_profile(marks, interests, q1, q2, q3, q4):
    sorted_subjects = sorted(marks.items(), key=lambda x: x[1], reverse=True)
    strengths = [subj for subj, _ in sorted_subjects[:2]]

    profile = {
        "strengths": strengths,
        "interests": interests,
        "favorite_subjects": [q3],
        "aspiration": q1,
        "work_preference": q2,
        "extra_curricular_details": q4
    }
    return profile
