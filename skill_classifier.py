import json
from typing import Dict, List
import spacy

class SkillClassifier:
    def __init__(self):
        """Initialize skill classifier with skills database and NLP model"""
        try:
            # Load skills from JSON file
            with open('skills.json', 'r') as f:
                self.skills_db = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load skills database: {str(e)}")
            self.skills_db = {}

        try:
            # Load spaCy model (small model is faster)
            self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            print(f"Warning: Could not load spaCy model: {str(e)}")
            self.nlp = None

        # Create regex patterns for all skills
        self.skill_patterns = {}
        self._create_skill_patterns()
        
        # Create skill context patterns
        self.context_patterns = self._create_context_patterns()
        
        # Initialize context window size
        self.context_window = 5  # Number of words to consider around a skill mention

    def _create_skill_patterns(self):
        """Create regex patterns for all skills in the database"""
        for category, skills in self.skills_db.items():
            if isinstance(skills, dict):
                # For nested categories
                for subcategory, tech_stack in skills.items():
                    for skill in tech_stack:
                        self._add_skill_pattern(skill)
            else:
                # For flat list of skills
                for skill in skills:
                    self._add_skill_pattern(skill)

    def _create_context_patterns(self):
        """Create patterns to identify skill-related context"""
        patterns = {
            'programming': r'\b(?:programming|development|coding|software)\b',
            'framework': r'\b(?:framework|library|platform)\b',
            'database': r'\b(?:database|sql|nosql|storage)\b',
            'cloud': r'\b(?:cloud|aws|azure|gcp|googlecloud|heroku|digitalocean)\b',
            'devops': r'\b(?:devops|ci/cd|continuous|deployment|infrastructure)\b',
            'ml': r'\b(?:machine|learning|ai|artificial|intelligence|deep|neural)\b'
        }
        return patterns

    def _add_skill_pattern(self, skill: str):
        """Add a skill pattern to the patterns dictionary"""
        # Clean skill name for regex
        clean_skill = skill.lower().replace(' ', '|').replace('.', '\.')
        if clean_skill not in self.skill_patterns:
            self.skill_patterns[clean_skill] = skill

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text to lowercase"""
        return text.lower()

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills and tech stacks from text with categorization using NLP"""
        try:
            # Preprocess text
            processed_text = text.lower()
            
            # Use spaCy for better context understanding
            if self.nlp:
                doc = self.nlp(text)
                
                # Find skill mentions with context
                found_skills = defaultdict(list)
                
                for token in doc:
                    # Check if token matches any skill pattern
                    for pattern in self.skill_patterns:
                        if re.search(pattern, token.text.lower()):
                            skill = self.skill_patterns[pattern]
                            category = self._find_skill_category(skill)
                            
                            if category:
                                # Get context around the skill
                                context = self._get_context(token, doc)
                                
                                # Use context to validate skill mention
                                if self._is_valid_skill_mention(skill, context):
                                    found_skills[category].append(skill)
                
                # Convert defaultdict to regular dict
                found_skills = dict(found_skills)
                
                # If no skills found using NLP, fall back to regex-only approach
                if not found_skills:
                    found_skills = self._extract_skills_regex(processed_text)
            else:
                # If spaCy is not available, use regex-only approach
                found_skills = self._extract_skills_regex(processed_text)
            
            # Remove duplicates and sort skills
            for category in found_skills:
                found_skills[category] = sorted(list(set(found_skills[category])))
            
            # Return empty dict if no skills found
            if not found_skills:
                return {"No skills found": []}
                
            return found_skills
            
        except Exception as e:
            print(f"Error extracting skills: {str(e)}")
            return {"Error extracting skills": []}

    def _extract_skills_regex(self, text: str) -> Dict[str, List[str]]:
        """Fallback regex-only skill extraction"""
        found_skills = defaultdict(list)
        
        for pattern in self.skill_patterns:
            if re.search(pattern, text):
                skill = self.skill_patterns[pattern]
                category = self._find_skill_category(skill)
                
                if category:
                    found_skills[category].append(skill)
        
        return dict(found_skills)

    def _get_context(self, token, doc):
        """Get context around a token"""
        start = max(0, token.i - self.context_window)
        end = min(len(doc) - 1, token.i + self.context_window)
        return [t.text.lower() for t in doc[start:end+1]]

    def _is_valid_skill_mention(self, skill: str, context: List[str]) -> bool:
        """Check if skill mention is valid based on context"""
        skill = skill.lower()
        
        # Check for common skill-related context
        for pattern in self.context_patterns.values():
            if any(re.search(pattern, word) for word in context):
                return True
        
        # Check if skill is used as a proper noun or tech term
        if any(word in context for word in ['using', 'knowledge', 'experience', 'familiarity']):
            return True
        
        # Check if skill is part of a tech stack mention
        if any(word in context for word in ['stack', 'framework', 'library', 'platform']):
            return True
            
        return False

    def _find_skill_category(self, skill: str) -> str:
        """Find which category a skill belongs to"""
        skill = skill.lower()
        for category, skills in self.skills_db.items():
            if isinstance(skills, dict):
                # For nested categories
                for subcategory, tech_stack in skills.items():
                    if skill in [s.lower() for s in tech_stack]:
                        return f"{category} - {subcategory}"
            else:
                # For flat list of skills
                if skill in [s.lower() for s in skills]:
                    return category
        return None