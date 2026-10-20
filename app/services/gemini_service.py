"""
Gemini AI Service for EngineerOS.

Real implementation using Google's Gemini API for skill-gap analysis
and personalized career roadmap generation. Falls back to MockAIService
if the API call fails for any reason.

The Gemini model name is read from Flask config (GEMINI_MODEL) and
is never hard-coded. The API key is read from the environment and
is never exposed in templates or frontend code.
"""
import json
import re
import traceback


class GeminiService:
    """Handles all communication with the Google Gemini AI API."""

    def __init__(self, api_key, model_name=None):
        """
        Initialize the Gemini service.

        Args:
            api_key (str): The Gemini API key from environment.
            model_name (str): Model identifier (e.g. 'gemini-2.0-flash').
                              Falls back to 'gemini-2.0-flash' if not provided.
        """
        import google.generativeai as genai

        self.api_key = api_key
        self.model_name = model_name or 'gemini-2.0-flash'

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _build_profile_summary(self, profile_data):
        """
        Build a human-readable text summary of the student's profile
        to include in the Gemini prompt.
        """
        lines = []
        lines.append(f"Student Name: {profile_data.get('name', 'N/A')}")
        lines.append(f"College: {profile_data.get('college', 'N/A')}")
        lines.append(f"Branch: {profile_data.get('branch', 'N/A')}")
        lines.append(f"Year: {profile_data.get('year', 'N/A')}")
        lines.append(f"CGPA: {profile_data.get('cgpa', 'N/A')}")
        lines.append(f"Target Career Role: {profile_data.get('target_role', 'N/A')}")
        lines.append(f"Preferred Domain: {profile_data.get('preferred_domain', 'N/A')}")
        lines.append(f"Career Timeline: {profile_data.get('career_timeline', 'N/A')}")
        lines.append(f"Target Companies: {profile_data.get('target_companies', 'N/A')}")

        skills = profile_data.get('skills', [])
        skill_levels = profile_data.get('skill_levels', {})
        if skills:
            skill_strings = []
            for s in skills:
                level = skill_levels.get(s, '')
                skill_strings.append(f"{s} ({level})" if level else s)
            lines.append(f"Current Skills: {', '.join(skill_strings)}")
        else:
            lines.append("Current Skills: None listed")

        interests = profile_data.get('interests', [])
        if interests:
            lines.append(f"Interests: {', '.join(interests)}")
        else:
            lines.append("Interests: None listed")

        return '\n'.join(lines)

    def _extract_json(self, text):
        """
        Extract a JSON object or array from the model's text response.
        Handles markdown code fences, leading/trailing prose, and both dicts & lists.
        """
        if not text:
            return None

        # 1. Try to extract JSON from markdown code fences first
        code_blocks = re.findall(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        for block in code_blocks:
            block = block.strip()
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                pass

        # 2. Try parsing the trimmed text directly
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # 3. Look for outermost array [ { ... } ]
        array_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        # 4. Look for outermost object { ... }
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _get_mock_fallback(self):
        """Return a MockAIService instance for fallback."""
        from app.services.mock_ai_service import MockAIService
        return MockAIService()

    def analyze_skills(self, profile_data):
        """
        Analyze a student's skills and identify gaps using Gemini AI.

        Sends a structured prompt to Gemini and parses the JSON response.
        Falls back to MockAIService if the API call or parsing fails.

        Args:
            profile_data (dict): Student profile data.

        Returns:
            dict: {strong_areas, gaps_identified, overall_readiness, recommendations}
        """
        profile_summary = self._build_profile_summary(profile_data)
        target_role = profile_data.get('target_role', 'Software Engineer')

        prompt = f"""You are a career advisor for engineering students in India.

Analyze this student's profile and determine their career readiness for the role of "{target_role}".

STUDENT PROFILE:
{profile_summary}

Respond ONLY with a valid JSON object (no markdown, no explanation) in exactly this format:
{{
    "strong_areas": ["skill1", "skill2", ...],
    "gaps_identified": ["missing_skill1", "missing_skill2", ...],
    "overall_readiness": <integer 0-100>,
    "recommendations": ["recommendation1", "recommendation2", ...]
}}

Rules:
- "strong_areas" should list the student's existing skills that are relevant to the target role.
- "gaps_identified" should list important skills the student is MISSING for the target role.
- "overall_readiness" should be a realistic percentage (0-100) of how ready the student is.
- "recommendations" should contain 2-4 specific, actionable career tips.
- Include 3-8 items in strong_areas and gaps_identified.
- Be realistic and helpful."""

        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json(response.text)

            if result and all(k in result for k in ['strong_areas', 'gaps_identified', 'overall_readiness']):
                # Ensure recommendations key exists
                if 'recommendations' not in result:
                    result['recommendations'] = []
                return result
            else:
                print(f"[GeminiService] Could not parse analysis response. Falling back to mock.")
                return self._get_mock_fallback().analyze_skills(profile_data)

        except Exception as e:
            print(f"[GeminiService] API error during analyze_skills: {e}")
            return self._get_mock_fallback().analyze_skills(profile_data)

    def generate_roadmap(self, profile_data):
        """
        Generate a personalized career roadmap using Gemini AI.

        Sends a structured prompt to Gemini requesting a phased roadmap
        with milestones, then parses the JSON response. Falls back to
        MockAIService if the API call or parsing fails.

        Args:
            profile_data (dict): Student profile data.

        Returns:
            dict: {title, target_role, estimated_duration, phases, skill_gap_analysis}
        """
        profile_summary = self._build_profile_summary(profile_data)
        target_role = profile_data.get('target_role', 'Software Engineer')
        timeline = profile_data.get('career_timeline', '6 months')
        student_name = profile_data.get('name', 'Student')

        prompt = f"""You are a career advisor for engineering students in India.

Generate a personalized career roadmap for this student who wants to become a "{target_role}".

STUDENT PROFILE:
{profile_summary}

Respond ONLY with a valid JSON object (no markdown, no explanation) in exactly this format:
{{
    "title": "Roadmap title here",
    "target_role": "{target_role}",
    "estimated_duration": "{timeline}",
    "skill_gap_analysis": {{
        "strong_areas": ["skill1", "skill2", ...],
        "gaps_identified": ["missing_skill1", "missing_skill2", ...],
        "overall_readiness": <integer 0-100>,
        "recommendations": ["tip1", "tip2", ...]
    }},
    "phases": [
        {{
            "phase_number": 1,
            "title": "Phase title",
            "duration": "X weeks",
            "milestones": [
                {{
                    "title": "Milestone title",
                    "description": "What the student should do",
                    "type": "learning",
                    "resources": ["https://example.com"]
                }}
            ]
        }}
    ]
}}

Rules:
- Create 3-4 phases ordered from foundations to career readiness.
- Each phase should have 3-4 milestones.
- Milestone "type" must be one of: "learning", "project", "practice", "assessment".
- "resources" should be real, helpful URLs (use popular sites like LeetCode, freeCodeCamp, Coursera, YouTube, GitHub).
- Tailor the roadmap specifically to the student's current skills, gaps, and target role.
- Be realistic about the timeline: "{timeline}".
- Make recommendations specific and actionable."""

        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json(response.text)

            if result and 'phases' in result and len(result.get('phases', [])) > 0:
                # Ensure all expected top-level keys exist
                if 'title' not in result:
                    result['title'] = f'{target_role} Career Roadmap for {student_name}'
                if 'target_role' not in result:
                    result['target_role'] = target_role
                if 'estimated_duration' not in result:
                    result['estimated_duration'] = timeline
                if 'skill_gap_analysis' not in result:
                    result['skill_gap_analysis'] = self.analyze_skills(profile_data)

                # Validate phase structure
                for i, phase in enumerate(result['phases']):
                    if 'phase_number' not in phase:
                        phase['phase_number'] = i + 1
                    if 'title' not in phase:
                        phase['title'] = f'Phase {i + 1}'
                    if 'duration' not in phase:
                        phase['duration'] = '4 weeks'
                    if 'milestones' not in phase:
                        phase['milestones'] = []

                    # Validate milestone structure
                    for milestone in phase['milestones']:
                        if 'title' not in milestone:
                            milestone['title'] = 'Untitled Milestone'
                        if 'description' not in milestone:
                            milestone['description'] = ''
                        if 'type' not in milestone or milestone['type'] not in ['learning', 'project', 'practice', 'assessment']:
                            milestone['type'] = 'learning'
                        if 'resources' not in milestone or not isinstance(milestone['resources'], list):
                            milestone['resources'] = []

                return result
            else:
                print(f"[GeminiService] Could not parse roadmap response. Falling back to mock.")
                return self._get_mock_fallback().generate_roadmap(profile_data)

        except Exception as e:
            print(f"[GeminiService] API error during generate_roadmap: {e}")
            return self._get_mock_fallback().generate_roadmap(profile_data)

    def generate_interview_questions(self, profile_data, gaps):
        """
        Generate mock interview questions based on the student's target role and skill gaps.
        """
        target_role = profile_data.get('target_role', 'Software Engineer')
        
        prompt = f"""You are an expert technical recruiter interviewing a candidate for a '{target_role}' role.
The candidate has the following skill gaps: {', '.join(gaps) if gaps else 'None specific'}.

Generate 3 to 5 interview questions. Include a mix of technical questions testing their knowledge and behavioral questions.
Focus especially on the skill gaps if applicable.

Respond ONLY with a valid JSON array of objects (no markdown, no explanation) in exactly this format:
[
    {{
        "id": 1,
        "question": "Question text here..."
    }},
    ...
]
"""
        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json(response.text)

            # Support dict wrapper like {"questions": [...]}
            if isinstance(result, dict) and 'questions' in result and isinstance(result['questions'], list):
                result = result['questions']

            if result and isinstance(result, list) and len(result) > 0:
                validated = []
                for idx, q in enumerate(result):
                    if isinstance(q, dict) and 'question' in q:
                        validated.append({
                            "id": q.get('id', idx + 1),
                            "question": q['question']
                        })
                if validated:
                    return validated

            print(f"[GeminiService] Could not parse interview questions. Falling back to mock.")
            return self._get_mock_fallback().generate_interview_questions(profile_data, gaps)

        except Exception as e:
            print(f"[GeminiService] API error during generate_interview_questions: {e}")
            return self._get_mock_fallback().generate_interview_questions(profile_data, gaps)

    def evaluate_interview_answers(self, questions, answers, target_role=None):
        """
        Evaluate student interview answers and provide structured feedback.
        """
        target_role = target_role or 'Software Engineer'

        # Format the Q&A for the prompt
        qa_pairs = []
        for idx, q in enumerate(questions):
            qid = str(q.get('id', idx + 1))
            qa_pairs.append({
                "id": qid,
                "question": q.get('question', ''),
                "answer": answers.get(qid, '')
            })

        prompt = f"""You are an expert technical interviewer evaluating a candidate for the role of '{target_role}'.

Candidate's Interview Submissions:
{json.dumps(qa_pairs, indent=2)}

TASK:
Evaluate each answer thoroughly based on technical correctness, clarity, depth, structure (such as the STAR method), and relevance to the '{target_role}' role.

Respond ONLY with a valid JSON array in exactly this schema:
[
  {{
    "id": "1",
    "score": <integer from 1 to 10>,
    "strengths": [
      "<specific strength citing details from their answer>",
      "<another specific strength>"
    ],
    "improvements": [
      "<specific, actionable area for improvement>",
      "<another specific improvement>"
    ],
    "feedback": "<2-3 sentence personalized evaluation addressing the candidate directly>"
  }}
]

RULES:
- Provide genuine, critical feedback.
- Scores must be integers between 1 and 10.
- Ensure 'strengths' and 'improvements' have 2 to 4 bullet points each.
- Reference actual details from the candidate's answer.
- Do NOT include any markdown or text outside the JSON array."""

        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json(response.text)

            # Support dict wrappers like {"evaluations": [...]} or {"feedback": [...]}
            if isinstance(result, dict):
                for key in ['evaluations', 'feedback', 'results', 'questions']:
                    if key in result and isinstance(result[key], list):
                        result = result[key]
                        break
                else:
                    if 'id' in result or 'score' in result:
                        result = [result]

            if result and isinstance(result, list) and len(result) > 0:
                results_by_id = {}
                for idx, r in enumerate(result):
                    if isinstance(r, dict):
                        r_id = str(r.get('id', idx + 1))
                        results_by_id[r_id] = r
                        results_by_id[f"idx_{idx}"] = r

                final_feedback = []
                for idx, q in enumerate(questions):
                    qid = str(q.get('id', idx + 1))
                    user_ans = answers.get(qid, '')
                    q_text = q.get('question', '')

                    eval_item = results_by_id.get(qid) or results_by_id.get(str(idx + 1)) or results_by_id.get(f"idx_{idx}") or {}

                    raw_score = eval_item.get('score', 6)
                    try:
                        score = int(raw_score)
                        if score > 10 and score <= 100:
                            score = round(score / 10)
                        score = max(1, min(10, score))
                    except (ValueError, TypeError):
                        score = 6

                    strengths = eval_item.get('strengths') or eval_item.get('strong_points') or []
                    if not isinstance(strengths, list):
                        strengths = [str(strengths)] if strengths else []
                    if not strengths:
                        strengths = ["Answered the prompt directly"]

                    improvements = eval_item.get('improvements') or eval_item.get('areas_for_improvement') or []
                    if not isinstance(improvements, list):
                        improvements = [str(improvements)] if improvements else []
                    if not improvements:
                        improvements = ["Could include more specific metrics or concrete implementation details"]

                    feedback_text = eval_item.get('feedback') or eval_item.get('overall_feedback') or eval_item.get('summary') or "Good effort. Review the suggested improvements to refine your response."

                    final_feedback.append({
                        "id": qid,
                        "question": q_text,
                        "answer": user_ans,
                        "score": score,
                        "strengths": [str(s) for s in strengths],
                        "improvements": [str(i) for i in improvements],
                        "feedback": str(feedback_text)
                    })

                return final_feedback

            print(f"[GeminiService] Could not parse interview evaluation. Falling back to mock.")
            return self._get_mock_fallback().evaluate_interview_answers(questions, answers, target_role=target_role)

        except Exception as e:
            print(f"[GeminiService] API error during evaluate_interview_answers: {e}")
            return self._get_mock_fallback().evaluate_interview_answers(questions, answers, target_role=target_role)

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
