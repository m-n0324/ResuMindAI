"""
Skill Extraction Module
Advanced skill extraction and analysis without external NLP libraries.
Categorizes skills and detects proficiency levels.
"""

import re
from typing import Dict, List, Tuple
from enum import Enum


class SkillCategory(str, Enum):
    """Skill categories"""
    PROGRAMMING = "programming"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    DATABASES = "databases"
    CLOUD = "cloud"
    DATA_SCIENCE = "data_science"
    TESTING = "testing"
    TOOLS = "tools"
    SOFT_SKILLS = "soft_skills"


class ProficiencyLevel(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill:
    """Represents an extracted skill with metadata"""
    
    def __init__(
        self, 
        name: str, 
        category: SkillCategory,
        proficiency: ProficiencyLevel = ProficiencyLevel.INTERMEDIATE
    ):
        self.name = name
        self.category = category
        self.proficiency = proficiency

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "category": self.category.value,
            "proficiency": self.proficiency.value
        }


class SkillCategoryExtractor:
    """Categorized skill extraction"""

    SKILL_CATEGORIES = {
        SkillCategory.PROGRAMMING: [
            'python', 'javascript', 'typescript', 'java', 'csharp', 'c++',
            'golang', 'rust', 'kotlin', 'swift', 'php', 'ruby', 'scala',
            'groovy', 'perl', 'r', 'haskell', 'clojure', 'elixir',
            'coffeescript', 'dart', 'julia', 'lua', 'matlab', 'vb', 'vbnet'
        ],
        SkillCategory.FRONTEND: [
            'html', 'css', 'react', 'angular', 'vue', 'svelte', 'bootstrap',
            'tailwind', 'sass', 'less', 'webpack', 'vite', 'parcel', 'rollup',
            'jquery', 'backbone', 'ember', 'preact', 'alpine', 'htmx',
            'nextjs', 'nuxt', 'remix', 'astro', 'sveltekit', 'gatsby'
        ],
        SkillCategory.BACKEND: [
            'node', 'express', 'fastapi', 'django', 'flask', 'spring',
            'aspnet', 'asp.net', 'rails', 'laravel', 'symfony', 'sinatra',
            'gin', 'echo', 'fiber', 'grpc', 'graphql', 'rest', 'restful',
            'graphiql', 'apollo', 'hasura', 'strapi', 'directus', 'supabase'
        ],
        SkillCategory.DATABASES: [
            'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'nosql',
            'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'firebase',
            'realtime database', 'firestore', 'sqlalchemy', 'orm', 'sqlite',
            'oracle', 'mssql', 'mariadb', 'couch', 'neo4j', 'graph database'
        ],
        SkillCategory.CLOUD: [
            'aws', 'ec2', 's3', 'lambda', 'rds', 'sqs', 'sns', 'cloudfront',
            'azure', 'cosmos', 'app service', 'gcp', 'cloud run', 'bigquery',
            'dataflow', 'heroku', 'vercel', 'netlify', 'render', 'railway',
            'digitalocean', 'linode', 'vultr', 'cloudflare', 'cloudinary'
        ],
        SkillCategory.DEVOPS: [
            'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'puppet',
            'chef', 'jenkins', 'circleci', 'gitlab', 'github', 'travis',
            'github actions', 'helm', 'argocd', 'flux', 'spinnaker', 'argo',
            'cloudformation', 'sam', 'cdk', 'pulumi', 'vagrant', 'compose',
            'nginx', 'apache', 'haproxy', 'prometheus', 'grafana', 'elk',
            'datadog', 'newrelic', 'splunk', 'cloudwatch', 'stackdriver'
        ],
        SkillCategory.DATA_SCIENCE: [
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'keras', 'scikit', 'sklearn', 'pandas', 'numpy', 'scipy',
            'matplotlib', 'seaborn', 'plotly', 'nlp', 'cv', 'computer vision',
            'bert', 'gpt', 'llm', 'huggingface', 'langchain', 'llama',
            'openai', 'gemini', 'anthropic', 'transformers', 'spacy', 'nltk',
            'jupyter', 'notebooks', 'anaconda', 'conda', 'pip', 'poetry',
            'statistics', 'probability', 'regression', 'classification',
            'clustering', 'dimensionality reduction', 'feature engineering'
        ],
        SkillCategory.TESTING: [
            'pytest', 'junit', 'unittest', 'rspec', 'mocha', 'jest', 'cypress',
            'selenium', 'testng', 'qat', 'qa', 'tdd', 'bdd', 'jasmine',
            'vitest', 'cucumber', 'behave', 'robot framework', 'appium',
            'load testing', 'jmeter', 'gatling', 'locust', 'postman', 'insomnia'
        ],
        SkillCategory.TOOLS: [
            'git', 'github', 'gitlab', 'bitbucket', 'svn', 'jira', 'confluence',
            'slack', 'figma', 'adobe xd', 'sketch', 'postman', 'insomnia',
            'vscode', 'vim', 'neovim', 'emacs', 'intellij', 'pycharm',
            'linux', 'unix', 'windows', 'macos', 'bash', 'shell', 'powershell'
        ],
        SkillCategory.SOFT_SKILLS: [
            'leadership', 'communication', 'teamwork', 'collaboration',
            'project management', 'agile', 'scrum', 'kanban', 'problem solving',
            'critical thinking', 'analysis', 'mentoring', 'coaching',
            'presentation', 'negotiation', 'conflict resolution', 'time management',
            'adaptability', 'creativity', 'innovation', 'strategic thinking'
        ]
    }

    PROFICIENCY_KEYWORDS = {
        ProficiencyLevel.EXPERT: ['expert', 'mastery', 'specialist', '15+ years', '10+ years'],
        ProficiencyLevel.ADVANCED: ['advanced', 'proficient', '5+ years', '7+ years', 'senior'],
        ProficiencyLevel.INTERMEDIATE: ['intermediate', 'working knowledge', '2+ years', '3+ years', 'mid-level'],
        ProficiencyLevel.BEGINNER: ['beginner', 'learning', 'familiar', '< 1 year', 'basic'],
    }

    @staticmethod
    def get_category_for_skill(skill: str) -> SkillCategory:
        """Get category for a skill"""
        skill_lower = skill.lower()
        
        for category, skills in SkillCategoryExtractor.SKILL_CATEGORIES.items():
            if skill_lower in skills or any(s in skill_lower for s in skills):
                return category
        
        # Default to tools for unknown skills
        return SkillCategory.TOOLS

    @staticmethod
    def detect_proficiency(text_around_skill: str) -> ProficiencyLevel:
        """
        Detect proficiency level from context around skill mention.
        
        Args:
            text_around_skill: Text snippet containing the skill
            
        Returns:
            Estimated proficiency level
        """
        text_lower = text_around_skill.lower()
        
        for level, keywords in SkillCategoryExtractor.PROFICIENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        
        return ProficiencyLevel.INTERMEDIATE  # Default

    @staticmethod
    def extract_skills_with_context(text: str) -> List[Skill]:
        """
        Extract skills with proficiency and category information.
        
        Args:
            text: Resume or JD text
            
        Returns:
            List of Skill objects with metadata
        """
        skills_dict = {}  # skill_name -> Skill object
        
        # Find each skill with surrounding context (50 chars before/after)
        for category, skill_list in SkillCategoryExtractor.SKILL_CATEGORIES.items():
            for skill_name in skill_list:
                # Case-insensitive search
                pattern = r'\b' + re.escape(skill_name) + r'\b'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    # Detect proficiency from context
                    proficiency = SkillCategoryExtractor.detect_proficiency(context)
                    
                    # Store skill (use highest proficiency if found multiple times)
                    if skill_name not in skills_dict:
                        skills_dict[skill_name] = Skill(
                            name=skill_name,
                            category=category,
                            proficiency=proficiency
                        )
                    else:
                        # Update if this occurrence has higher proficiency
                        proficiency_order = [
                            ProficiencyLevel.BEGINNER,
                            ProficiencyLevel.INTERMEDIATE,
                            ProficiencyLevel.ADVANCED,
                            ProficiencyLevel.EXPERT
                        ]
                        if (proficiency_order.index(proficiency) > 
                            proficiency_order.index(skills_dict[skill_name].proficiency)):
                            skills_dict[skill_name].proficiency = proficiency
        
        return list(skills_dict.values())

    @staticmethod
    def extract_skills_by_category(text: str) -> Dict[str, List[str]]:
        """
        Extract skills organized by category.
        
        Args:
            text: Resume or JD text
            
        Returns:
            Dictionary: category -> list of skills
        """
        skills = SkillCategoryExtractor.extract_skills_with_context(text)
        
        result = {category.value: [] for category in SkillCategory}
        
        for skill in skills:
            result[skill.category.value].append(skill.name)
        
        # Remove empty categories
        return {k: v for k, v in result.items() if v}

    @staticmethod
    def get_skill_gap_analysis(
        resume_text: str,
        jd_text: str
    ) -> Dict:
        """
        Analyze skill gaps between resume and JD.
        
        Args:
            resume_text: Resume text
            jd_text: Job description text
            
        Returns:
            Dict with gap analysis results
        """
        resume_skills = SkillCategoryExtractor.extract_skills_with_context(resume_text)
        jd_skills = SkillCategoryExtractor.extract_skills_with_context(jd_text)
        
        resume_skill_names = {s.name for s in resume_skills}
        jd_skill_names = {s.name for s in jd_skills}
        
        missing_skills = jd_skill_names - resume_skill_names
        extra_skills = resume_skill_names - jd_skill_names
        matched_skills = resume_skill_names & jd_skill_names
        
        return {
            "matched_skills": sorted(list(matched_skills)),
            "missing_skills": sorted(list(missing_skills)),
            "extra_skills": sorted(list(extra_skills)),
            "match_percentage": (len(matched_skills) / len(jd_skill_names) * 100) if jd_skill_names else 0,
            "resume_skill_count": len(resume_skill_names),
            "jd_skill_count": len(jd_skill_names),
        }
