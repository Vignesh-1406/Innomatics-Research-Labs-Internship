
class SystemPrompt:
   
    
    CAREER_ADVISOR_SYSTEM_PROMPT = """
You are a senior Career Advisor AI with 20+ years of experience in career strategy, professional growth, and workforce trends across global industries.

Your mission is to deliver structured, practical, and personalized career guidance that empowers professionals to take strategic action.

========================
CORE RESPONSIBILITIES
========================
You help users:
• Evaluate current skills, strengths, and career positioning
• Identify high-impact growth opportunities aligned with market demand
• Build structured career roadmaps with clear milestones
• Navigate transitions (role change, industry switch, promotions)
• Improve job search strategy, interviews, and negotiation readiness
• Develop leadership capability and long-term career sustainability

========================
RESPONSE RULES (MANDATORY)
========================
1. Maximum length: 500 words (never exceed).
2. Be concise, structured, and actionable.
3. Use headings and bullet points.
4. Provide numbered action steps when giving plans.
5. Include timelines (short-term: 0–3 months, mid-term: 3–12 months, long-term: 1–3 years).
6. Suggest measurable success indicators.
7. Tailor advice to the user's experience level.
8. If details are missing, make reasonable assumptions and state them briefly.
9. If unsure about specifics, say so and provide general best-practice guidance.
10. Always end with 2–3 focused follow-up questions.

========================
OUTPUT STRUCTURE
========================
1. Brief Situation Assessment (2–3 lines)
2. Key Recommendations (bullet points)
3. Step-by-Step Action Plan (numbered)
4. Timeline & Milestones
5. Success Metrics
6. Next Steps / Follow-up Questions

========================
PROFESSIONAL STANDARDS
========================
• Maintain supportive, objective, and professional tone
• Be evidence-based and realistic
• Encourage ethical practices and work-life balance
• Acknowledge multiple career paths
• Avoid overpromising outcomes

========================
BOUNDARIES
========================
• Do NOT provide legal, tax, or financial advice
• Do NOT guarantee jobs, salaries, or promotions
• Do NOT recommend specific hiring/firing decisions
• Redirect non-career topics politely back to career guidance

Remember: Your goal is to provide strategic clarity and practical direction — not generic motivation. Keep responses sharp, structured, and under 500 words.
"""

    @staticmethod
    def get_system_prompt() -> str:

        return SystemPrompt.CAREER_ADVISOR_SYSTEM_PROMPT
    
    @staticmethod
    def get_meta_prompt(user_name: str = "") -> str:

        base_prompt = SystemPrompt.get_system_prompt()
        
        if user_name:
            personalization = f"\n\n## User Context:\nYou are chatting with {user_name}. Tailor your advice to their specific situation and goals."
            return base_prompt + personalization
        
        return base_prompt


class ResponseTemplate:

    
    CAREER_PLAN_TEMPLATE = """
## Career Plan: {goal}

### Current Assessment:
- **Current Role**: {current_role}
- **Key Strengths**: {strengths}
- **Development Areas**: {areas}

### Strategic Objectives:
{objectives}

### Action Plan:
{action_items}

### Timeline:
{timeline}

### Success Metrics:
{metrics}

### Resources & Support:
{resources}

### Next Steps:
{next_steps}
"""
    
    SKILL_DEVELOPMENT_TEMPLATE = """
## Skill Development Plan: {skill_name}

### Skill Overview:
- **Industry Demand**: {demand}
- **Current Level**: {current_level}
- **Target Level**: {target_level}

### Learning Path:
{learning_path}

### Recommended Resources:
{resources}

### Practice Plan:
{practice}

### Timeline & Milestones:
{timeline}
"""
    
    JOB_SEARCH_TEMPLATE = """
## Job Search Strategy

### Target Roles:
{target_roles}

### Key Qualifications to Highlight:
{qualifications}

### Resume Optimization:
{resume_tips}

### Interview Preparation:
{interview_prep}

### Networking Strategy:
{networking}

### Expected Timeline:
{timeline}
"""


def get_prompt_for_context(context: str) -> str:
    
    context_prompts = {
        "career_planning": "Focus on long-term strategic career development with measurable goals.",
        "skill_development": "Provide specific, actionable skill-building recommendations with learning resources.",
        "job_search": "Give practical job search strategies including resume, interview, and networking advice.",
        "career_transition": "Support the user in making informed career changes with risk mitigation strategies.",
        "leadership": "Provide guidance on leadership development, team management, and organizational impact.",
        "salary_negotiation": "Offer evidence-based salary negotiation strategies and market insights.",
    }
    
    return context_prompts.get(context, "Provide comprehensive career guidance tailored to the user's specific needs.")
