"""
Embeddings and Semantic Similarity Module
Provides JD-Resume semantic matching without external embedding services.
Uses TF-IDF and cosine similarity for lightweight, local solution.
"""

from typing import Dict, List, Tuple
from collections import Counter
import math
import re


class SimpleEmbedding:
    """
    Simple TF-IDF based embedding for semantic similarity.
    Works locally without external dependencies or API calls.
    """

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenize text into keywords.
        Removes common stop words and normalizes.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Common stop words to ignore
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'have', 'has', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'shall', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'what', 'which', 'who', 'whom', 'when', 'where',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'same', 'so',
            'than', 'too', 'very', 'just', 'also', 'still', 'through', 'between'
        }
        
        # Convert to lowercase and split
        text = text.lower()
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s\+\#]', ' ', text)
        
        # Split into tokens
        tokens = text.split()
        
        # Filter: remove short tokens and stop words, keep tech terms
        filtered = [
            token for token in tokens 
            if len(token) > 2 and token not in stop_words
        ]
        
        return filtered

    @staticmethod
    def calculate_tf(tokens: List[str]) -> Dict[str, float]:
        """
        Calculate Term Frequency for tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Dictionary of token: frequency
        """
        if not tokens:
            return {}
        
        token_count = Counter(tokens)
        total = len(tokens)
        
        return {token: count / total for token, count in token_count.items()}

    @staticmethod
    def cosine_similarity(tf1: Dict[str, float], tf2: Dict[str, float]) -> float:
        """
        Calculate cosine similarity between two TF dictionaries.
        
        Args:
            tf1: Term frequency dict 1
            tf2: Term frequency dict 2
            
        Returns:
            Similarity score (0-1)
        """
        if not tf1 or not tf2:
            return 0.0
        
        # Get all unique terms
        all_terms = set(tf1.keys()) | set(tf2.keys())
        
        # Create vectors
        vec1 = [tf1.get(term, 0.0) for term in all_terms]
        vec2 = [tf2.get(term, 0.0) for term in all_terms]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        
        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (mag1 * mag2)
        
        return float(similarity)

    @staticmethod
    def compute_similarity(text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts (0-100 scale).
        
        Args:
            text1: First text (e.g., resume)
            text2: Second text (e.g., job description)
            
        Returns:
            Similarity score (0-100)
        """
        # Tokenize both texts
        tokens1 = SimpleEmbedding.tokenize(text1)
        tokens2 = SimpleEmbedding.tokenize(text2)
        
        # Calculate TF
        tf1 = SimpleEmbedding.calculate_tf(tokens1)
        tf2 = SimpleEmbedding.calculate_tf(tokens2)
        
        # Calculate cosine similarity
        similarity = SimpleEmbedding.cosine_similarity(tf1, tf2)
        
        # Convert to 0-100 scale
        return similarity * 100


class SkillExtractor:
    """Extract and match skills from resume and JD"""

    # Curated list of common tech and professional skills
    COMMON_SKILLS = {
        # Programming Languages
        'python', 'javascript', 'typescript', 'java', 'csharp', 'c++', 'golang',
        'rust', 'kotlin', 'swift', 'objectivec', 'php', 'ruby', 'scala', 'groovy',
        
        # Web Technologies
        'html', 'css', 'react', 'angular', 'vue', 'svelte', 'node', 'express',
        'fastapi', 'django', 'flask', 'spring', 'asp.net', 'aspnet',
        'nextjs', 'nuxt', 'webpack', 'vite', 'graphql', 'rest', 'restful',
        'soap', 'grpc', 'websocket', 'websockets',
        
        # Databases
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'nosql',
        'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'firebase',
        'sqlalchemy', 'orm', 'sqlite', 'oracle', 'mssql', 'mariadb',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform',
        'jenkins', 'gitlab', 'github', 'circleci', 'travis', 'devops',
        'ansible', 'chef', 'puppet', 'cloudformation', 'heroku', 'vercel',
        'netlify', 'render', 'railway', 'digitalocean',
        
        # Data & ML
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
        'scikit', 'sklearn', 'pandas', 'numpy', 'scipy', 'matplotlib',
        'seaborn', 'plotly', 'nlp', 'cv', 'computer vision', 'ai',
        'bert', 'gpt', 'llm', 'huggingface', 'langchain', 'llama', 'openai',
        'gemini', 'anthropic', 'transformers', 'spacy', 'nltk',
        
        # Testing & QA
        'junit', 'pytest', 'testing', 'unittest', 'rspec', 'mocha', 'jest',
        'cypress', 'selenium', 'testng', 'qat', 'qa', 'tdd', 'bdd',
        
        # Other Tools
        'git', 'linux', 'unix', 'bash', 'shell', 'vim', 'vscode',
        'jira', 'confluence', 'slack', 'figma', 'xd', 'postman',
        'docker', 'nginx', 'apache', 'linux', 'windows', 'macos',
        
        # Soft Skills (high-level only)
        'leadership', 'communication', 'teamwork', 'project management',
        'agile', 'scrum', 'kanban', 'waterfall', 'problem solving',
        'analysis', 'critical thinking', 'mentoring', 'coaching',
        'presentation', 'negotiation', 'collaboration'
    }

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Extract known skills from text.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of detected skills
        """
        text_lower = text.lower()
        
        # Match skills
        detected = []
        for skill in SkillExtractor.COMMON_SKILLS:
            # Use word boundaries to avoid partial matches
            if f' {skill} ' in f' {text_lower} ':
                detected.append(skill)
            elif f' {skill},' in f' {text_lower},':
                detected.append(skill)
            elif f' {skill}.' in f' {text_lower}.':
                detected.append(skill)
            elif text_lower.startswith(skill + ' '):
                detected.append(skill)
            elif text_lower.endswith(' ' + skill):
                detected.append(skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for skill in detected:
            if skill not in seen:
                seen.add(skill)
                unique.append(skill)
        
        return unique

    @staticmethod
    def find_missing_skills(
        resume_text: str, 
        jd_text: str
    ) -> Tuple[List[str], List[str]]:
        """
        Find skills in JD that are missing from resume.
        
        Args:
            resume_text: Resume text
            jd_text: Job description text
            
        Returns:
            Tuple of (resume_skills, missing_skills)
        """
        resume_skills = set(SkillExtractor.extract_skills(resume_text))
        jd_skills = set(SkillExtractor.extract_skills(jd_text))
        
        missing = list(jd_skills - resume_skills)
        
        return list(resume_skills), missing
