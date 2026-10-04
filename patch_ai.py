import re

mock_methods = """
    def generate_project_recommendations(self, profile_data):
        target_role = profile_data.get('target_role', 'Software Engineer')
        return [
            {
                "title": f"AI Resume Analyzer for {target_role}",
                "description": "A full-stack application that analyzes resumes using AI.",
                "difficulty": "Intermediate",
                "estimated_time": "2-3 weeks",
                "technologies": ["Python", "Flask", "OpenAI"],
                "skills": ["Python", "Backend", "AI Integration"],
                "justification": "This project builds your AI and backend skills which are crucial for your target role."
            },
            {
                "title": "Expense Tracker",
                "description": "A robust financial tracking tool with data visualization.",
                "difficulty": "Beginner",
                "estimated_time": "1 week",
                "technologies": ["JavaScript", "HTML", "CSS"],
                "skills": ["Frontend", "UI/UX", "Data Visualization"],
                "justification": "A great starting point for frontend fundamentals."
            }
        ]

    def generate_project_roadmap(self, project_data, profile_data):
        return [
            {
                "stage": "Planning",
                "tasks": [
                    {"title": "Requirements Gathering", "description": "Define the scope", "required_skills": ["Product Management"], "estimated_hours": 2},
                    {"title": "System Design", "description": "Design the architecture", "required_skills": ["System Design"], "estimated_hours": 4}
                ]
            },
            {
                "stage": "Development",
                "tasks": [
                    {"title": "Backend Setup", "description": "Initialize Flask app", "required_skills": ["Python", "Flask"], "estimated_hours": 4},
                    {"title": "Frontend Setup", "description": "Create UI", "required_skills": ["HTML", "CSS"], "estimated_hours": 6}
                ]
            }
        ]

    def project_assistant(self, question, project_context):
        return {"response": f"This is a simulated AI response to your question: '{question}'. For a real answer, please configure the Gemini API key."}
"""

gemini_methods = """
    def generate_project_recommendations(self, profile_data):
        target_role = profile_data.get('target_role', 'Software Engineer')
        skills = profile_data.get('skills', [])
        prompt = f'''You are an expert AI career coach.
Based on the student's target role of '{target_role}' and their current skills: {', '.join(skills)},
generate 3 realistic project recommendations.

Respond ONLY with a valid JSON array of objects (no markdown, no explanation) in this format:
[
  {{
    "title": "Project Title",
    "description": "Short description of what to build.",
    "difficulty": "Beginner|Intermediate|Advanced",
    "estimated_time": "1-2 weeks",
    "technologies": ["Python", "Flask", "OpenAI"],
    "skills": ["API Design", "Database", "Python"],
    "justification": "Why this project helps them reach their career goal and close skill gaps."
  }}
]
'''
        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json(response.text)
            if result and isinstance(result, list):
                return result
            return self._get_mock_fallback().generate_project_recommendations(profile_data)
        except Exception as e:
            print(f"[GeminiService] API error: {e}")
            return self._get_mock_fallback().generate_project_recommendations(profile_data)

    def generate_project_roadmap(self, project_data, profile_data):
        prompt = f'''You are an expert technical project manager.
Create a step-by-step roadmap for building this project:
Title: {project_data.get('title')}
Description: {project_data.get('description')}
Technologies: {', '.join(project_data.get('technologies', []))}

Respond ONLY with a valid JSON array of objects (no markdown) in exactly this format:
[
  {{
    "stage": "Planning",
    "tasks": [
      {{
        "title": "Task title",
        "description": "Task description",
        "required_skills": ["Skill1", "Skill2"],
        "estimated_hours": 2
      }}
    ]
  }},
  {{
    "stage": "Development",
    "tasks": [
      {{
        "title": "Task title",
        "description": "Task description",
        "required_skills": ["Skill1", "Skill2"],
        "estimated_hours": 4
      }}
    ]
  }}
]
'''
        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json(response.text)
            if result and isinstance(result, list):
                return result
            return self._get_mock_fallback().generate_project_roadmap(project_data, profile_data)
        except Exception as e:
            print(f"[GeminiService] API error: {e}")
            return self._get_mock_fallback().generate_project_roadmap(project_data, profile_data)

    def project_assistant(self, question, project_context):
        prompt = f'''You are an AI programming assistant helping a student with their project.
Project Context:
Title: {project_context.get('title')}
Stage: {project_context.get('stage', 'Unknown')}
Technologies: {', '.join(project_context.get('technologies', []))}

Student Question: {question}

Provide a helpful, educational response. Do not write all the code for them, but explain concepts, suggest debugging steps, and provide small code snippets if needed. Use Markdown formatting.
'''
        try:
            response = self.model.generate_content(prompt)
            return {"response": response.text}
        except Exception as e:
            print(f"[GeminiService] API error: {e}")
            return self._get_mock_fallback().project_assistant(question, project_context)
"""

with open("C:/Users/Kunal/.gemini/antigravity/scratch/engineeros/app/services/mock_ai_service.py", "a") as f:
    f.write(mock_methods)

with open("C:/Users/Kunal/.gemini/antigravity/scratch/engineeros/app/services/gemini_service.py", "a") as f:
    f.write(gemini_methods)
