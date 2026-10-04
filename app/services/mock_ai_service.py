"""
Mock AI Service for EngineerOS.

Returns realistic, profile-aware mock data for development and testing.
No API key required. The app uses this automatically when no Gemini
API key is configured in .env.

The mock data is dynamic — it reads the student's actual target role
and existing skills to produce contextually relevant responses.
"""


# ─── Skill databases keyed by target role ──────────────────────────────
# Each entry lists the skills typically needed for that career path.
ROLE_SKILL_MAPS = {
    'Full Stack Developer': [
        'HTML/CSS', 'JavaScript', 'React', 'Node.js', 'Python',
        'SQL', 'REST APIs', 'Git', 'Docker', 'System Design'
    ],
    'Full Stack Web Developer': [
        'HTML/CSS', 'JavaScript', 'React', 'Node.js', 'Python',
        'SQL', 'REST APIs', 'Git', 'Docker', 'System Design'
    ],
    'Frontend Developer': [
        'HTML/CSS', 'JavaScript', 'TypeScript', 'React', 'Vue.js',
        'Responsive Design', 'CSS Frameworks', 'Git', 'Testing', 'Web Performance'
    ],
    'Backend Developer': [
        'Python', 'Java', 'SQL', 'REST APIs', 'PostgreSQL',
        'Redis', 'Docker', 'Linux', 'System Design', 'Git'
    ],
    'AI/ML Engineer': [
        'Python', 'NumPy', 'Pandas', 'Scikit-learn', 'TensorFlow',
        'Deep Learning', 'NLP', 'Statistics', 'SQL', 'Git'
    ],
    'Data Scientist': [
        'Python', 'Pandas', 'NumPy', 'Statistics', 'Machine Learning',
        'Data Visualization', 'SQL', 'Jupyter', 'Scikit-learn', 'Communication'
    ],
    'Cloud Architect': [
        'AWS/Azure/GCP', 'Docker', 'Kubernetes', 'Terraform', 'Linux',
        'Networking', 'CI/CD', 'Security', 'Python', 'System Design'
    ],
    'DevOps Engineer': [
        'Linux', 'Docker', 'Kubernetes', 'CI/CD', 'Git',
        'Terraform', 'AWS/Azure', 'Python', 'Monitoring', 'Scripting'
    ],
    'Mobile App Developer': [
        'Java', 'Kotlin', 'Flutter', 'Dart', 'REST APIs',
        'Firebase', 'UI/UX Design', 'Git', 'SQLite', 'State Management'
    ],
    'Cybersecurity Analyst': [
        'Networking', 'Linux', 'Python', 'Cryptography', 'OWASP',
        'Penetration Testing', 'Firewalls', 'SIEM', 'Compliance', 'Scripting'
    ],
    'Software Engineer': [
        'Data Structures', 'Algorithms', 'Python', 'Java', 'SQL',
        'System Design', 'OOP', 'Git', 'Testing', 'Problem Solving'
    ],
}

# Fallback for roles not in the map above
DEFAULT_REQUIRED_SKILLS = [
    'Data Structures', 'Algorithms', 'Python', 'SQL', 'Git',
    'System Design', 'OOP', 'REST APIs', 'Problem Solving', 'Communication'
]


# ─── Phase templates keyed by target role ──────────────────────────────
# Each phase has milestones with title, description, type, and resources.
ROLE_ROADMAP_TEMPLATES = {
    'default': [
        {
            'title': 'Foundation — Core CS Fundamentals',
            'duration': '4–6 weeks',
            'milestones': [
                {
                    'title': 'Data Structures & Algorithms Basics',
                    'description': 'Study arrays, linked lists, stacks, queues, trees, and basic sorting algorithms. Solve 20+ easy problems.',
                    'type': 'learning',
                    'resources': ['https://leetcode.com/explore/', 'https://www.geeksforgeeks.org/data-structures/']
                },
                {
                    'title': 'Object-Oriented Programming',
                    'description': 'Learn classes, inheritance, polymorphism, and design patterns. Apply them in a mini project.',
                    'type': 'learning',
                    'resources': ['https://realpython.com/python3-object-oriented-programming/']
                },
                {
                    'title': 'Version Control with Git & GitHub',
                    'description': 'Master branching, merging, pull requests, and collaborative workflows.',
                    'type': 'practice',
                    'resources': ['https://learngitbranching.js.org/', 'https://docs.github.com/en/get-started']
                },
                {
                    'title': 'Build a CLI Project',
                    'description': 'Create a command-line tool that demonstrates DSA and OOP concepts.',
                    'type': 'project',
                    'resources': []
                }
            ]
        },
        {
            'title': 'Core Skills — Domain-Specific Learning',
            'duration': '6–8 weeks',
            'milestones': [
                {
                    'title': 'Learn Primary Technology Stack',
                    'description': 'Deep-dive into the core language and framework for your target role. Build 2–3 small projects.',
                    'type': 'learning',
                    'resources': []
                },
                {
                    'title': 'Database & SQL Mastery',
                    'description': 'Study relational databases, write complex queries, and understand indexing and normalization.',
                    'type': 'learning',
                    'resources': ['https://sqlbolt.com/', 'https://mode.com/sql-tutorial/']
                },
                {
                    'title': 'REST API Development',
                    'description': 'Build a REST API with authentication, CRUD operations, and proper error handling.',
                    'type': 'project',
                    'resources': ['https://restfulapi.net/']
                },
                {
                    'title': 'Coding Practice Sprint',
                    'description': 'Solve 50+ medium-level problems on LeetCode or HackerRank. Focus on time complexity.',
                    'type': 'practice',
                    'resources': ['https://leetcode.com/', 'https://www.hackerrank.com/']
                }
            ]
        },
        {
            'title': 'Applied Skills — Real-World Projects',
            'duration': '4–6 weeks',
            'milestones': [
                {
                    'title': 'Build a Portfolio Project',
                    'description': 'Design and build a complete full-featured project that demonstrates your target role skills. Deploy it publicly.',
                    'type': 'project',
                    'resources': ['https://github.com/', 'https://vercel.com/', 'https://render.com/']
                },
                {
                    'title': 'System Design Fundamentals',
                    'description': 'Study scalability, load balancing, caching, database sharding, and microservices architecture.',
                    'type': 'learning',
                    'resources': ['https://github.com/donnemartin/system-design-primer']
                },
                {
                    'title': 'Open Source Contribution',
                    'description': 'Find a beginner-friendly open source project and make at least one meaningful contribution.',
                    'type': 'project',
                    'resources': ['https://goodfirstissue.dev/', 'https://github.com/firstcontributions/first-contributions']
                }
            ]
        },
        {
            'title': 'Career Readiness — Interview & Placement Prep',
            'duration': '3–4 weeks',
            'milestones': [
                {
                    'title': 'Resume & LinkedIn Optimization',
                    'description': 'Craft an ATS-friendly resume. Optimize LinkedIn with project showcases and skill endorsements.',
                    'type': 'assessment',
                    'resources': ['https://www.overleaf.com/latex/templates/tagged/cv']
                },
                {
                    'title': 'Mock Interview Practice',
                    'description': 'Complete 5+ mock interviews covering DSA, system design, and behavioral questions.',
                    'type': 'practice',
                    'resources': ['https://www.pramp.com/', 'https://interviewing.io/']
                },
                {
                    'title': 'Apply to Target Companies',
                    'description': 'Submit applications to your target companies. Tailor each resume and cover letter.',
                    'type': 'assessment',
                    'resources': []
                }
            ]
        }
    ]
}


class MockAIService:
    """
    Provides realistic, profile-aware mock AI responses for offline
    development and testing. No API key required.
    """

    def _get_required_skills(self, target_role):
        """Look up the expected skills for a target role."""
        if not target_role:
            return DEFAULT_REQUIRED_SKILLS

        # Try exact match first, then partial match
        for role_key, skills in ROLE_SKILL_MAPS.items():
            if role_key.lower() == target_role.lower():
                return skills
        for role_key, skills in ROLE_SKILL_MAPS.items():
            if role_key.lower() in target_role.lower() or target_role.lower() in role_key.lower():
                return skills

        return DEFAULT_REQUIRED_SKILLS

    def analyze_skills(self, profile_data):
        """
        Analyze a student's skills against their target role.

        Compares the student's existing skills with the required skills
        for their target role and computes a readiness score.

        Args:
            profile_data (dict): Student profile, skills, interests, goals.

        Returns:
            dict: {strong_areas, gaps_identified, overall_readiness, recommendations}
        """
        target_role = profile_data.get('target_role', 'Software Engineer')
        student_skills = [s.lower() for s in profile_data.get('skills', [])]
        required_skills = self._get_required_skills(target_role)

        # Compute strong areas and gaps
        strong_areas = []
        gaps_identified = []

        for skill in required_skills:
            if skill.lower() in student_skills:
                strong_areas.append(skill)
            else:
                gaps_identified.append(skill)

        # Also include student skills not in the required list as strengths
        for skill_name in profile_data.get('skills', []):
            if skill_name not in strong_areas:
                # Check if it's a case-insensitive match
                already_listed = any(s.lower() == skill_name.lower() for s in strong_areas)
                if not already_listed:
                    strong_areas.append(skill_name)

        # Calculate readiness score
        if len(required_skills) > 0:
            match_ratio = len([s for s in required_skills if s.lower() in student_skills]) / len(required_skills)
        else:
            match_ratio = 0
        overall_readiness = min(95, int(match_ratio * 100))

        # Generate recommendations
        recommendations = []
        if gaps_identified:
            recommendations.append(f'Focus on learning {gaps_identified[0]} first — it is critical for {target_role} roles.')
        if len(gaps_identified) > 2:
            recommendations.append(f'You have {len(gaps_identified)} skill gaps to close. Consider an online course or bootcamp.')
        if overall_readiness >= 60:
            recommendations.append('You are making good progress! Start applying for internships to gain real-world experience.')
        else:
            recommendations.append('Build 2-3 portfolio projects to demonstrate your growing skill set.')

        return {
            'strong_areas': strong_areas,
            'gaps_identified': gaps_identified,
            'overall_readiness': overall_readiness,
            'recommendations': recommendations
        }

    def generate_roadmap(self, profile_data):
        """
        Generate a complete personalized career roadmap.

        Returns a roadmap with phases and milestones, plus the
        skill-gap analysis embedded within it.

        Args:
            profile_data (dict): Student profile, skills, interests, goals.

        Returns:
            dict: {title, target_role, estimated_duration, phases, skill_gap_analysis}
        """
        target_role = profile_data.get('target_role', 'Software Engineer')
        timeline = profile_data.get('career_timeline', '6 months')
        student_name = profile_data.get('name', 'Student')

        # 1. Run skill analysis first
        analysis = self.analyze_skills(profile_data)

        # 2. Build roadmap structure from templates
        phases_template = ROLE_ROADMAP_TEMPLATES.get('default', [])

        phases = []
        for i, phase_data in enumerate(phases_template, start=1):
            milestones = []
            for m in phase_data['milestones']:
                milestones.append({
                    'title': m['title'],
                    'description': m['description'],
                    'type': m['type'],
                    'resources': m.get('resources', [])
                })

            phases.append({
                'phase_number': i,
                'title': phase_data['title'],
                'duration': phase_data['duration'],
                'milestones': milestones
            })

        # 3. Customize the roadmap title
        title = f'{target_role} Career Roadmap for {student_name}'

        return {
            'title': title,
            'target_role': target_role,
            'estimated_duration': timeline if timeline else '6 months',
            'phases': phases,
            'skill_gap_analysis': analysis
        }

    def generate_interview_questions(self, profile_data, gaps):
        """
        Generate mock interview questions.
        """
        target_role = profile_data.get('target_role', 'Software Engineer')
        return [
            {
                "id": 1,
                "question": f"Can you describe a challenging problem you solved related to {target_role}?"
            },
            {
                "id": 2,
                "question": f"How do you plan to bridge your skill gaps in: {', '.join(gaps[:2])}?"
            },
            {
                "id": 3,
                "question": "Where do you see yourself in 3 years in your engineering career?"
            }
        ]

    def evaluate_interview_answers(self, questions, answers):
        """
        Evaluate answers and provide mock feedback.
        """
        results = []
        for q in questions:
            qid = str(q.get('id'))
            ans = answers.get(qid, '')
            results.append({
                "id": qid,
                "question": q.get('question', ''),
                "answer": ans,
                "score": 7 if len(ans) > 10 else 3,
                "strengths": ["Attempted the question", "Clear formatting"],
                "improvements": ["Could be more detailed", "Provide concrete examples"],
                "feedback": "This is a solid start, but adding specific metrics or examples would make it much stronger." if len(ans) > 10 else "Your answer is too short. Try the STAR method."
            })
        return results

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
