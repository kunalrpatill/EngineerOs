"""
Mock AI Service for EngineerOS.

Returns realistic, profile-aware mock data for development and testing.
No API key required. The app uses this automatically when no Gemini
API key is configured in .env.

The mock data is dynamic — it reads the student's actual target role
and existing skills to produce contextually relevant responses.
"""
import re


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
        Generate mock interview questions based on target role and identified skill gaps.
        """
        target_role = profile_data.get('target_role', 'Software Engineer')
        required_skills = self._get_required_skills(target_role)
        primary_skill = required_skills[0] if required_skills else 'Software Engineering'

        # Q2 depends on whether gaps are available
        if gaps:
            gap_text = ', '.join(gaps[:2])
            q2_text = f"How do you plan to bridge your identified skill gaps in {gap_text}?"
        else:
            secondary_skill = required_skills[1] if len(required_skills) > 1 else 'System Design'
            q2_text = f"How do you stay up-to-date with emerging tools and best practices in {secondary_skill}?"

        return [
            {
                "id": 1,
                "question": f"Can you describe a challenging technical problem or project you tackled involving {primary_skill} for a {target_role} role?"
            },
            {
                "id": 2,
                "question": q2_text
            },
            {
                "id": 3,
                "question": "Tell me about a time you had to diagnose a difficult bug or handle a high-priority deadline. Walk through your problem-solving process."
            }
        ]

    def evaluate_interview_answers(self, questions, answers, target_role=None):
        """
        Intelligently analyze student interview answers and provide dynamic, structured feedback.
        Evaluates depth, technical vocabulary, structure (STAR method), quantifiable results,
        and relevance to the student's target role.
        """
        target_role = target_role or 'Software Engineer'
        role_skills = [s.lower() for s in self._get_required_skills(target_role)]

        tech_keywords_map = {
            'backend': [
                'api', 'rest', 'graphql', 'database', 'sql', 'nosql', 'postgres', 'postgresql',
                'mysql', 'mongodb', 'redis', 'cache', 'caching', 'index', 'indexing', 'query',
                'microservices', 'monolith', 'server', 'async', 'concurrency', 'threading',
                'latency', 'throughput', 'load balancer', 'queue', 'kafka', 'rabbitmq', 'scalable',
                'scalability', 'sharding', 'orm', 'middleware', 'endpoint'
            ],
            'frontend': [
                'react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css', 'dom',
                'state management', 'redux', 'hook', 'component', 'responsive', 'ui', 'ux',
                'accessibility', 'webpack', 'vite', 'tailwind', 'bootstrap', 'render', 'browser'
            ],
            'aiml': [
                'model', 'training', 'dataset', 'overfitting', 'underfitting', 'loss', 'accuracy',
                'precision', 'recall', 'f1', 'feature', 'gradient', 'neural network', 'pytorch',
                'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'nlp', 'transformer', 'pipeline',
                'regression', 'classification', 'clustering', 'cross-validation'
            ],
            'devops': [
                'docker', 'container', 'kubernetes', 'k8s', 'ci/cd', 'pipeline', 'jenkins',
                'github actions', 'terraform', 'aws', 'azure', 'gcp', 'cloud', 'linux',
                'monitoring', 'prometheus', 'grafana', 'deploy', 'deployment', 'nginx', 'ssl'
            ],
            'fundamentals': [
                'algorithm', 'data structure', 'array', 'linked list', 'tree', 'graph',
                'hash map', 'hash table', 'stack', 'queue', 'heap', 'sorting', 'binary search',
                'time complexity', 'space complexity', 'big o', 'o(n)', 'o(1)', 'o(log n)',
                'recursion', 'dynamic programming', 'pointer', 'memory'
            ],
            'practices': [
                'git', 'branch', 'pull request', 'unit test', 'integration test', 'test driven',
                'tdd', 'mock', 'clean code', 'solid', 'refactor', 'oop', 'design pattern',
                'debugging', 'profiling', 'security', 'authentication', 'authorization', 'jwt',
                'edge case', 'error handling', 'exception', 'logging'
            ]
        }

        star_patterns = {
            'situation': [
                r'\bsituation\b', r'\bproblem\s+was\b', r'\bproject\s+was\b', r'\bchallenge\s+was\b',
                r'\bwhen\s+i\s+was\b', r'\bneeded\s+to\b', r'\bworking\s+on\b',
                r'\bfaced\s+(?:an?\s+)?(?:issue|obstacle|bug|challenge)\b', r'\bin\s+my\s+(?:previous|semester|last)\b'
            ],
            'task': [
                r'\bmy\s+task\b', r'\bmy\s+role\b', r'\bresponsible\s+for\b', r'\bobjective\s+was\b',
                r'\bgoal\s+was\b', r'\bhad\s+to\s+(?:deliver|solve|build|implement)\b', r'\brequirement\b'
            ],
            'action': [
                r'\bi\s+(?:implemented|built|designed|developed|refactored|investigated|optimized|used|created|resolved|wrote|analyzed|chose|selected|migrated)\b'
            ],
            'result': [
                r'\b(?:as\s+a\s+)?result\b', r'\boutcome\b', r'\bachieved\b', r'\bsuccessfully\b',
                r'\bdecreased\s+by\b', r'\bincreased\s+by\b', r'\breduced\s+by\b', r'\bimproved\s+by\b',
                r'\bdropped\s+by\b', r'\bin\s+the\s+end\b', r'\bdelivered\b', r'\blearned\b'
            ]
        }

        metric_patterns = [
            r'\b\d+(?:\.\d+)?%',
            r'\b\d+(?:\.\d+)?\s*(?:ms|seconds|minutes|hrs|hours|days|weeks)\b',
            r'\b\d+(?:\.\d+)?x\b',
            r'\b\d+(?:,\d+)?\s*(?:users|requests|qps|queries|rps|records|rows|mb|gb|tb)\b',
            r'\b(?:reduced|improved|increased|dropped|boosted|cut)\s+(?:by\s+)?\d+'
        ]

        results = []
        for q in questions:
            qid = str(q.get('id', '1'))
            ans = answers.get(qid, '').strip()
            q_text = q.get('question', '')

            words = re.findall(r'\b[a-zA-Z0-9_-]+\b', ans.lower())
            word_count = len(words)
            unique_words = len(set(words))
            ans_lower = ans.lower()

            # Detect technical keywords
            detected_tech = []
            for cat, kw_list in tech_keywords_map.items():
                for kw in kw_list:
                    if re.search(r'\b' + re.escape(kw) + r'\b', ans_lower):
                        title_kw = kw.title()
                        if title_kw not in detected_tech:
                            detected_tech.append(title_kw)
            for skill in role_skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', ans_lower):
                    title_skill = skill.title()
                    if title_skill not in detected_tech:
                        detected_tech.append(title_skill)

            # Detect STAR components
            star_found = {}
            for phase, patterns in star_patterns.items():
                star_found[phase] = any(re.search(pat, ans_lower) for pat in patterns)
            star_count = sum(1 for v in star_found.values() if v)

            # Detect metrics
            detected_metrics = []
            for pat in metric_patterns:
                found = re.findall(pat, ans_lower)
                for f in found:
                    if f not in detected_metrics:
                        detected_metrics.append(f)

            # Detect quality / best practice signals
            mentions_testing = any(re.search(r'\b' + re.escape(t) + r'\b', ans_lower) for t in ['test', 'tests', 'testing', 'unit test', 'integration test', 'qa', 'validate'])
            mentions_edge_cases = any(re.search(r'\b' + re.escape(t) + r'\b', ans_lower) for t in ['edge case', 'edge cases', 'error handling', 'exception', 'failure', 'fallback'])
            mentions_tradeoffs = any(re.search(r'\b' + re.escape(t) + r'\b', ans_lower) for t in ['trade-off', 'tradeoff', 'tradeoffs', 'alternative', 'instead of', 'pros and cons', 'considered'])

            # Compute Score (1 to 10)
            if word_count < 10:
                score = 2
            elif word_count < 25:
                score = 4
            elif word_count < 60:
                score = 6
            elif word_count < 120:
                score = 7
            else:
                score = 8

            # Modifiers based on content
            if len(detected_tech) >= 4:
                score += 1
            elif len(detected_tech) >= 2:
                score += 0.5
            elif len(detected_tech) == 0 and word_count >= 25:
                score -= 1

            if star_count >= 3:
                score += 1
            elif star_count >= 2:
                score += 0.5

            if len(detected_metrics) >= 1:
                score += 1

            if mentions_testing or mentions_edge_cases:
                score += 0.5

            if mentions_tradeoffs:
                score += 0.5

            # Penalize excessive repetition / spam
            if word_count >= 20 and (unique_words / max(word_count, 1)) < 0.40:
                score -= 3

            score = int(round(max(1, min(10, score))))

            # Strengths
            strengths = []
            if detected_tech:
                top_tech = detected_tech[:3]
                strengths.append(f"Demonstrated solid technical depth referencing domain concepts: {', '.join(top_tech)}.")
            if star_count >= 3 or (star_found['action'] and star_found['result']):
                strengths.append("Structured narrative effectively using the STAR method (clear context, action, and outcome).")
            if detected_metrics:
                strengths.append(f"Backed up accomplishments with quantitative metrics ({', '.join(detected_metrics[:2])}).")
            if mentions_testing or mentions_edge_cases:
                strengths.append("Demonstrated engineering rigor by addressing testing, validation, or edge cases.")
            if mentions_tradeoffs:
                strengths.append("Articulated technical reasoning and trade-offs behind your chosen solution.")
            if word_count >= 70 and not strengths:
                strengths.append("Provided a detailed and articulate explanation with clear contextual background.")
            if not strengths:
                strengths.append("Addressed the prompt directly with a clear and concise response.")
            if len(strengths) < 2:
                strengths.append("Good baseline communication of problem-solving intent.")

            # Improvements
            improvements = []
            if not detected_metrics:
                improvements.append("Quantify your impact: include measurable figures (e.g., latency reduction, throughput, user count).")
            if not star_found['result']:
                improvements.append("Highlight the 'Result' phase: clearly state what measurable outcome or organizational value was delivered.")
            if len(detected_tech) < 3:
                improvements.append(f"Incorporate more domain-specific technologies and architectural patterns relevant to {target_role}.")
            if not (mentions_testing or mentions_edge_cases):
                improvements.append("Address reliability: explain how you tested your solution and handled edge cases or failures.")
            if not mentions_tradeoffs:
                improvements.append("Discuss alternative approaches: explain why you chose this design over other potential solutions.")
            if word_count < 40:
                improvements.append("Expand on your individual contribution: walk through your personal decisions and the specific technical hurdles overcome.")
            if word_count > 250:
                improvements.append("Keep the response concise: focus on high-impact architectural choices rather than granular implementation steps.")
            if not improvements:
                improvements.append("Consider practicing live delivery to keep this strong response concise and impactful.")
            improvements = improvements[:3]

            # Overall Feedback
            if score >= 8:
                feedback_text = (
                    f"Excellent answer for a {target_role} role! You conveyed genuine technical expertise, "
                    f"clear structure, and actionable problem solving. Focusing on the minor improvement points "
                    f"above will make your delivery stellar in top-tier interviews."
                )
            elif score >= 5:
                feedback_text = (
                    f"Solid foundational response for a {target_role} position. You explained the overarching idea well, "
                    f"but technical interviewers will look for deeper implementation details, quantifiable outcomes, "
                    f"and a tighter STAR framework structure."
                )
            else:
                feedback_text = (
                    f"This response needs more depth and technical rigor for a {target_role} interview. "
                    f"Avoid high-level summaries: detail the exact problem, the technologies utilized, your specific actions, "
                    f"and the concrete results achieved using the STAR method."
                )

            results.append({
                "id": qid,
                "question": q_text,
                "answer": ans,
                "score": score,
                "strengths": strengths,
                "improvements": improvements,
                "feedback": feedback_text
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
