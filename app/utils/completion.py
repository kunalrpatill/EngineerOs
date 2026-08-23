"""
Profile completion percentage calculator.
Calculates a 0-100% score based on how completely a student
has filled in their academic details, career goals, skills, and links.
"""

def calculate_profile_completion(profile, skills=None, interests=None):
    """
    Calculate the profile completion percentage.
    
    Args:
        profile (Profile): The student's profile model instance.
        skills (list): Optional list of Skill objects or count.
        interests (list): Optional list of Interest objects or count.
        
    Returns:
        int: Completion score between 0 and 100.
    """
    if not profile:
        return 0
        
    score = 0
    
    # 1. Academic Details (25 points total)
    if profile.college and profile.college.strip():
        score += 5
    if profile.branch and profile.branch.strip():
        score += 5
    if profile.year:
        score += 5
    if profile.semester:
        score += 5
    if profile.cgpa and float(profile.cgpa) > 0:
        score += 5
        
    # 2. Career Goals (30 points total)
    if profile.target_role and profile.target_role.strip():
        score += 10
    if profile.preferred_domain and profile.preferred_domain.strip():
        score += 10
    if profile.career_timeline and profile.career_timeline.strip():
        score += 5
    if profile.target_companies and profile.target_companies.strip():
        score += 5
        
    # 3. External Profiles (15 points total)
    if profile.github_url and profile.github_url.strip():
        score += 5
    if profile.linkedin_url and profile.linkedin_url.strip():
        score += 5
    if profile.leetcode_url and profile.leetcode_url.strip():
        score += 5
        
    # 4. Technical Skills & Interests (30 points total)
    skill_count = len(skills) if skills is not None else (len(profile.user.skills) if (profile.user and profile.user.skills) else 0)
    interest_count = len(interests) if interests is not None else (len(profile.user.interests) if (profile.user and profile.user.interests) else 0)
    
    if skill_count >= 1:
        score += 10
    if skill_count >= 3:
        score += 10
    if interest_count >= 1:
        score += 10
        
    return min(100, score)
