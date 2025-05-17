import os
import re
import json
import logging
from typing import Dict, List, Tuple
import PyPDF2
import pdfplumber
import spacy
from spacy.matcher import Matcher
import nltk
from nltk.corpus import stopwords

# Set up logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load skills data
with open('skills.json', 'r') as f:
    SKILLS_DATA = json.load(f)

class PDFExtractor:
    def __init__(self):
        """Initialize the PDF extractor"""
        try:
            # Initialize NLP
            try:
                import spacy
                self.nlp = spacy.load('en_core_web_sm')
            except Exception as e:
                print(f"Warning: Could not load spacy model: {str(e)}")
                self.nlp = None
            
            # Initialize NLTK
            try:
                import nltk
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('wordnet', quiet=True)
            except Exception as e:
                print(f"Warning: Could not download NLTK data: {str(e)}")
            
            # Initialize matcher if NLP is available
            if self.nlp:
                try:
                    from spacy.matcher import Matcher
                    self.matcher = Matcher(self.nlp.vocab)
                except Exception as e:
                    print(f"Warning: Could not initialize matcher: {str(e)}")
                    self.matcher = None
            
            # Initialize skill classifier
            try:
                from skill_classifier import SkillClassifier
                self.skill_classifier = SkillClassifier()
            except Exception as e:
                print(f"Warning: Could not initialize skill classifier: {str(e)}")
                self.skill_classifier = None
            

        except Exception as e:
            print(f"Warning: Could not load NLP models: {str(e)}")
            self.nlp = None

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from a PDF file with multiple methods and clean formatting"""
        try:
            if not pdf_path or not os.path.exists(pdf_path):
                raise ValueError(f"Invalid PDF path: {pdf_path}")
            
            # Try pdfplumber first
            try:
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        try:
                            # Extract text with layout analysis
                            page_text = page.extract_text(layout=True)
                            
                            # Clean up text while preserving important formatting
                            if page_text:
                                # Remove excessive newlines but preserve paragraphs
                                page_text = re.sub(r'\n\s*\n\s*\n', '\n\n', page_text)  # Remove triple newlines
                                page_text = re.sub(r'\n\s*\n', '\n', page_text)  # Normalize double newlines
                                
                                # Remove extra spaces but preserve single spaces
                                page_text = re.sub(r'\s{2,}', ' ', page_text)  # Remove multiple spaces
                                
                                # Remove empty lines but preserve paragraph breaks
                                page_text = '\n'.join(line for line in page_text.splitlines() if line.strip() or line == '')
                                
                                # Preserve potential names and proper nouns
                                page_text = re.sub(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', r'\1', page_text)
                                
                                text += page_text + "\n"
                        except Exception as e:
                            # Fallback to basic extraction if layout fails
                            page_text = page.extract_text()
                            if page_text:
                                page_text = re.sub(r'\n\s*\n\s*\n', '\n\n', page_text)
                                page_text = re.sub(r'\n\s*\n', '\n', page_text)
                                page_text = re.sub(r'\s{2,}', ' ', page_text)
                                page_text = '\n'.join(line for line in page_text.splitlines() if line.strip() or line == '')
                                page_text = re.sub(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', r'\1', page_text)
                                
                                text += page_text + "\n"
                
                # Final cleanup while preserving structure
                text = text.strip()  # Remove leading/trailing whitespace
                text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove triple newlines
                text = re.sub(r'\n\s*\n', '\n', text)  # Normalize double newlines
                
                # Preserve potential names in the final text
                text = re.sub(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', r'\1', text)
                
                return text
            
            except Exception as e:
                print(f"Warning: pdfplumber failed: {str(e)}")
                try:
                    # Fallback to PyPDF2
                    with open(pdf_path, 'rb') as file:
                        try:
                            pdf_reader = PyPDF2.PdfReader(file)
                            text = ""
                            for page in pdf_reader.pages:
                                try:
                                    page_text = page.extract_text()
                                    if page_text:
                                        # Clean up text
                                        page_text = re.sub(r'\n\s*\n', '\n', page_text)
                                        page_text = re.sub(r'\s+', ' ', page_text)
                                        page_text = '\n'.join(line for line in page_text.splitlines() if line.strip())
                                        
                                        text += page_text + "\n"
                                except Exception as e:
                                    print(f"Warning: Failed to extract page: {str(e)}")
                                    continue
                            
                            # Final cleanup
                            text = text.strip()
                            text = re.sub(r'\n\s*\n', '\n\n', text)
                            
                            return text
                        except Exception as e:
                            print(f"Warning: Failed to read PDF: {str(e)}")
                            raise
                except Exception as e:
                    print(f"Warning: PyPDF2 failed: {str(e)}")
                    raise
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")

    def extract_skills(self, text: str) -> List[Dict[str, List[str]]]:
        """Extract skills from text using skills.json database"""
        try:
            # Load skills from JSON file
            with open('skills.json', 'r') as f:
                skills_db = json.load(f)

            # Initialize found skills
            found_skills = []
            lines = text.lower().split('\n')
            
            # Look for common skill section keywords
            skill_keywords = ['skills', 'technical skills', 'key skills', 'expertise', 'technologies', 'technical expertise']
            
            # Find skill section
            skill_section_start = None
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in skill_keywords):
                    skill_section_start = i
                    break
            
            # If we found a skill section, only look in that section
            if skill_section_start is not None:
                skill_section = lines[skill_section_start:skill_section_start + 20]
                text_to_search = ' '.join(skill_section)
            else:
                text_to_search = text.lower()
            
            # Split by common separators
            text_to_search = text_to_search.replace(',', ' ').replace('.', ' ').replace(':', ' ').replace(';', ' ')
            
            # Search for skills in each category
            for category, skills in skills_db.items():
                category_skills = []
                
                for skill in skills:
                    skill_words = skill.lower().split()
                    
                    # Handle multi-word skills
                    skill_text = ' '.join(skill_words)
                    
                    # Check if skill exists in text
                    if skill_text in text_to_search:
                        category_skills.append(skill)
                    
                    # Also check for variations with spaces
                    skill_variations = [''.join(skill_words), '_'.join(skill_words)]
                    for variation in skill_variations:
                        if variation in text_to_search:
                            category_skills.append(skill)
                            break
                
                # If we found any skills in this category
                if category_skills:
                    found_skills.append({
                        "category": category,
                        "tech_stack": list(set(category_skills))  # Remove duplicates
                    })
            
            # Sort categories alphabetically
            found_skills.sort(key=lambda x: x["category"])
            
            # If no skills found
            if not found_skills:
                return [{"category": "No skills found", "tech_stack": []}]
            
            return found_skills
            
        except Exception as e:
            print(f"Error extracting skills: {str(e)}")
            return [{"category": "Error extracting skills", "tech_stack": []}]
        
    def extract_name(self, text: str) -> str:
        """Extract name from text using multiple methods and heuristics"""
        try:
            # Extract email first to use as reference
            email = self.extract_email(text)
            email_parts = email.split('@')[0].lower() if '@' in email else ''
            
            # Get font sizes and formatting information
            font_sizes = []
            bold_texts = []
            
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[0]  # Only look at first page
                words = page.extract_words()
                for word in words:
                    if 'size' in word:
                        font_sizes.append(word['size'])
                    if 'fontname' in word and word['fontname'].lower() == 'bold':
                        bold_texts.append(word['text'])
            
            # Find the largest font size
            max_font_size = max(font_sizes) if font_sizes else 0
            
            # Try to find name in the first few lines
            lines = text.split('\n')
            
            # Check each line in the first 5 lines
            for line in lines[:5]:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip if it looks like a section header
                if any(keyword in line.lower() for keyword in ['resume', 'cv', 'profile', 'summary']):
                    continue
                    
                # Try to find a name pattern
                match = re.search(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line)  # First Last
                if match:
                    name = match.group(0)
                    
                    # Validate against email if available
                    if email:
                        name_parts = name.lower().replace(' ', '').replace('.', '')
                        if name_parts in email_parts:
                            return name
                    
                    # Check formatting cues
                    if name in bold_texts:
                        return name
                    
                    # Check if it's in the largest font
                    if max_font_size > 0:
                        for word in words:
                            if 'size' in word and word['size'] == max_font_size:
                                if word['text'] in name:
                                    return name
            
            # If no name found yet, try to extract from email
            if email:
                # Try to extract name from email
                email_name = email_parts.split('.')[0]
                if email_name and email_name != 'info' and email_name != 'contact':
                    # Capitalize first letter of each word
                    name = ' '.join(word.capitalize() for word in email_name.split('_'))
                    
                    # Check if it looks like a valid name
                    if len(name.split()) <= 3 and not any(char.isdigit() for char in name):
                        return name
            
            # If no name found yet, try to extract from first line
            if lines:
                first_line = lines[0].strip()
                if first_line:
                    # Try to find a name at the start of the first line
                    match = re.search(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', first_line)
                    if match:
                        name = match.group(0)
                        if len(name.split()) <= 3:
                            return name
            
            # If all else fails, return a default name
            return "Candidate Name"
            
        except Exception as e:
            print(f"Error extracting name: {str(e)}")
            return "Candidate Name"                          

    def extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        try:
            # Try multiple phone number patterns
            patterns = [
                r'\+?[0-9]{1,3}[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # International format
                r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # Local format
                r'[0-9]{10}',  # 10-digit format
                r'[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'  # Custom format
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    phone = match.group(0)
                    # Clean up the phone number
                    phone = re.sub(r'[^0-9+]', '', phone)
                    return phone
            
            return ""
            
        except Exception as e:
            print(f"Error extracting phone: {str(e)}")
            return ""

    def generate_resume_summary(self, name: str, skills: list, experience: list) -> str:
        """Generate a professional summary using Python's text processing"""
        try:
            # Get unique skills from all categories
            all_skills = set()
            for skill_dict in skills:
                if isinstance(skill_dict, dict) and "tech_stack" in skill_dict:
                    all_skills.update(skill_dict["tech_stack"])
            
            # Get recent experience
            recent_experience = []
            for exp in experience:
                if isinstance(exp, dict):
                    recent_experience.append(f"{exp.get('position', '')} at {exp.get('company', '')}")
            
            # Prepare summary context
            context = {
                "name": name or "Candidate",
                "experience": experience[:3],  # Top 3 positions
                "skills": list(all_skills),  # All skills
                "years_of_experience": len(experience)  # Total experience entries
            }
            
            # Generate summary using Python's text processing
            summary_parts = []
            
            # Add name
            if name:
                summary_parts.append(f"Hi, I'm {name}")
            
            # Add years of experience
            if context["years_of_experience"] > 0:
                years = context["years_of_experience"]
                experience_str = f"with {years} years of professional experience"
                summary_parts.append(experience_str)
            
            # Add experience positions
            if experience:
                exp_str = ", ".join([f"{exp.get('position', '')} at {exp.get('company', '')}" for exp in experience[:2]])  # Take first 2 positions
                summary_parts.append(f"working as {exp_str}")
            
            # Add skills
            if all_skills:
                skill_list = list(all_skills)
                
                # Categorize skills
                tech_skills = [s for s in skill_list if s.lower() in SKILLS_DATA.get("technical_skills", [])]
                business_skills = [s for s in skill_list if s.lower() in SKILLS_DATA.get("business_skills", [])]
                soft_skills = [s for s in skill_list if s.lower() in SKILLS_DATA.get("soft_skills", [])]
                
                # Add technical skills
                if tech_skills:
                    tech_str = ", ".join(tech_skills[:3]) + (" and more" if len(tech_skills) > 3 else "")
                    summary_parts.append(f"with expertise in {tech_str}")
                
                # Add business skills if any
                if business_skills:
                    biz_str = ", ".join(business_skills[:3]) + (" and more" if len(business_skills) > 3 else "")
                    summary_parts.append(f"and strong business acumen in {biz_str}")
                
                # Add soft skills if any
                if soft_skills:
                    soft_str = ", ".join(soft_skills[:3]) + (" and more" if len(soft_skills) > 3 else "")
                    summary_parts.append(f"with excellent {soft_str}")
            
            # Add professional attributes
            if context["years_of_experience"] > 5:
                summary_parts.append("demonstrating strong leadership and technical acumen")
            elif context["years_of_experience"] > 2:
                summary_parts.append("showing rapid professional growth and skill development")
            else:
                summary_parts.append("with a solid foundation in professional practices")
            
            # Combine all parts
            summary = " ".join(summary_parts)
            if summary:
                return summary + "."
            else:
                return "No information available to generate summary"
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Error generating summary"

    def extract_email(self, text: str) -> str:
        """Extract email address from text"""
        # Define email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Try to find email using pattern
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)
        return ""

    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience using NLP and semantic analysis"""
        experience = []
        
        try:
            # Load spaCy model
            import spacy
            nlp = spacy.load('en_core_web_sm')
            
            # Process text with spaCy
            doc = nlp(text)
            
            # Keywords to identify experience sections
            exp_keywords = [
                'experience', 'work experience', 'professional experience',
                'employment history', 'career history', 'professional background',
                'work history', 'employment', 'career',
                'professional summary', 'career summary', 'employment details'
            ]
            
            # Common position keywords
            position_keywords = [
                'engineer', 'developer', 'manager', 'analyst', 'consultant',
                'specialist', 'lead', 'director', 'architect', 'administrator',
                'coordinator', 'assistant', 'associate', 'senior', 'junior',
                'principal', 'technical', 'business', 'product', 'project',
                'operations', 'quality', 'security', 'data', 'cloud', 'devops',
                'software', 'application', 'system', 'network', 'database',
                'frontend', 'backend', 'full stack', 'mobile', 'web'
            ]
            
            # Common company patterns
            company_patterns = [
                r'\b(?:at|with|for|in|to)\s+(\w+(?:\s+\w+)*)',  # at/with Company
                r'\b(?:company|organization|firm|employer):\s*(\w+(?:\s+\w+)*)',  # company: Company
                r'\b(?:at|in|for|with)\s+(\w+(?:\s+\w+)*)',  # at/in/for/with Company
                r'\b(?:company|organization|firm)\s*:\s*(\w+(?:\s+\w+)*)'  # company/organization/firm: Company
            ]

            # Date and duration patterns
            date_patterns = [
                r'(?:\d{1,2}/\d{4}|\d{1,2}-\d{4}|\d{1,2}\s*[\./-]\d{4})',  # 03/2014, 03-2014, 03.2014
                r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}',  # jan 2014
                r'(?:january|february|march|april|may|june|july|august|september|october|november|december)[a-z]*\s*\d{4}',  # january 2014
                r'\d{4}',  # 2014
            ]

            duration_patterns = [
                r'(\d{1,2}/\d{4}\s*[-–]\s*\d{1,2}/\d{4})',  # 03/2014 - 10/2018
                r'(\d{1,2}-\d{4}\s*[-–]\s*\d{1,2}-\d{4})',  # 03-2014 - 10-2018
                r'(\d{1,2}\s*[\./]\d{4}\s*[-–]\s*\d{1,2}\s*[\./]\d{4})',  # 03.2014 - 10.2018
                r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}\s*[-–]\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4})',  # jan 2014 - dec 2018
                r'(\d{4}\s*[-–]\s*\d{4})',  # 2014 - 2018
                r'(\d{4}\s*[-–]\s*present|\d{4}\s*[-–]\s*current)',  # 2014 - present
                r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}\s*[-–]\s*present',  # jan 2014 - present
                r'(?:january|february|march|april|may|june|july|august|september|october|november|december)[a-z]*\s*\d{4}\s*[-–]\s*present'  # january 2014 - present
            ]

            # Try to extract experience section using NLP
            try:
                # Find experience section
                exp_section = None
                experience_section = []
                
                # Find experience section
                for sent in doc.sents:
                    if any(keyword in sent.text.lower() for keyword in exp_keywords):
                        exp_section = sent
                        break
                
                if exp_section:
                    # Collect all sentences in the experience section
                    for sent in doc.sents:
                        if exp_section.start <= sent.start <= exp_section.end:
                            experience_section.append(sent.text)
                        elif any(keyword in sent.text.lower() for keyword in [
                            'education', 'skills', 'certifications', 'projects',
                            'achievements', 'publications', 'languages', 'interests',
                            'summary', 'objective', 'profile', 'contact', 'address'
                        ]):
                            break
                    
                    # Process the experience section line by line
                    current_experience = {
                        'company': None,
                        'position': None,
                        'duration': None,
                        'location': None
                    }
                    
                    def finalize_experience():
                        if current_experience['company'] and current_experience['position']:
                            experience.append({
                                'company': current_experience['company'],
                                'position': current_experience['position'],
                                'duration': current_experience['duration'] or 'Duration not specified',
                                'location': current_experience['location'] or 'Location not specified'
                            })
                            return True
                        return False
                    
                    for line in experience_section:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Reset current experience if we find a new position
                        if finalize_experience() and any(keyword in line.lower() for keyword in position_keywords):
                            current_experience = {
                                'company': None,
                                'position': None,
                                'duration': None,
                                'location': None
                            }
                            
                        # Extract position
                        if not current_experience['position']:
                            for keyword in position_keywords:
                                if keyword in line.lower():
                                    position = line.split('-')[0].split(',')[0].strip()
                                    position = position.replace('•', '').strip()
                                    current_experience['position'] = position
                                    break
                        
                        # Extract company
                        if not current_experience['company']:
                            for ent in nlp(line).ents:
                                if ent.label_ in ['ORG', 'ORGANIZATION']:
                                    current_experience['company'] = ent.text
                                    break
                        
                        # Extract duration
                        if not current_experience['duration']:
                            for pattern in duration_patterns:
                                match = re.search(pattern, line.lower())
                                if match:
                                    current_experience['duration'] = match.group(1)
                                    break
                        
                        # Extract location
                        if not current_experience['location']:
                            location_match = re.search(r'([A-Za-z\s]+,\s*[A-Z]{2})', line)
                            if location_match:
                                current_experience['location'] = location_match.group(1)
                    
                    # Finalize last experience
                    finalize_experience()
                    
            except Exception as e:
                print(f"Error processing experience with NLP: {str(e)}")
                # Fallback to pattern matching approach
                lines = text.split('\n')
                current_company = None
                current_position = None
                current_duration = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Remove bullet points
                    if line.startswith('•') or line.startswith('-'):
                        line = line[1:].strip()
                        
                    # Check for company names using patterns
                    for pattern in company_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            current_company = match.group(1)
                            continue
                            
                    # Check for position keywords
                    if any(keyword in line.lower() for keyword in position_keywords):
                        current_position = line
                        continue
                        
                    # Check for duration
                current_position = None
                current_duration = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Remove bullet points
                    if line.startswith('•') or line.startswith('-'):
                        line = line[1:].strip()
                        
                    # Check for company names using patterns
                    for pattern in company_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            current_company = match.group(1)
                            continue
                            
                    # Check for position keywords
                    if any(keyword in line.lower() for keyword in position_keywords):
                        current_position = line
                        continue
                        
                    # Check for duration
                    if any(word in line.lower() for word in [
                        'year', 'month', 'present', 'january', 'february',
                        'march', 'april', 'may', 'june', 'july', 'august',
                        'september', 'october', 'november', 'december'
                    ]):
                        current_duration = line
                        continue
                        
                    # If we have all components, create an entry
                    if current_company and current_position:
                        experience.append({
                            'company': current_company,
                            'position': current_position,
                            'duration': current_duration if current_duration else 'Duration not specified'
                        })
                        current_company = None
                        current_position = None
                        current_duration = None

        except ImportError:
            print("Error: spaCy is required for experience extraction. Please install it first.")
            return []
        except OSError:
            print("Error: spaCy model 'en_core_web_sm' is not installed. Please download it first.")
            return []

        return experience
