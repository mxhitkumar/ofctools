import re
from collections import Counter
from django.utils import timezone
from .models import ATSAnalysis

class ATSAnalyzer:
    """
    Analyzes resume content against job descriptions for ATS optimization.
    Provides keyword matching, formatting checks, and improvement suggestions.
    """
    
    def __init__(self, resume, job_description):
        self.resume = resume
        self.job_description = job_description.lower()
        self.resume_text = self._extract_resume_text().lower()
        
        # Common stop words to exclude from keyword analysis
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
    
    def _extract_resume_text(self):
        """Extract all text content from resume"""
        text_parts = [
            self.resume.full_name,
            self.resume.email,
            self.resume.summary,
        ]
        
        # Add experience descriptions
        for exp in self.resume.experiences.all():
            text_parts.extend([
                exp.company,
                exp.position,
                exp.description
            ])
        
        # Add education
        for edu in self.resume.educations.all():
            text_parts.extend([
                edu.institution,
                edu.field_of_study,
                edu.get_degree_display()
            ])
        
        # Add skills
        for skill in self.resume.skills.all():
            text_parts.append(skill.name)
        
        # Add certifications
        for cert in self.resume.certifications.all():
            text_parts.extend([
                cert.name,
                cert.issuing_organization
            ])
        
        # Add projects
        for proj in self.resume.projects.all():
            text_parts.extend([
                proj.title,
                proj.description,
                proj.technologies
            ])
        
        return ' '.join(filter(None, text_parts))
    
    def _extract_keywords(self, text, min_length=3, max_keywords=50):
        """Extract meaningful keywords from text"""
        # Remove special characters and split into words
        words = re.findall(r'\b[a-z]{' + str(min_length) + r',}\b', text)
        
        # Filter out stop words
        keywords = [w for w in words if w not in self.stop_words]
        
        # Count frequency
        word_freq = Counter(keywords)
        
        # Return most common keywords
        return dict(word_freq.most_common(max_keywords))
    
    def _extract_required_skills(self):
        """Extract technical skills and requirements from job description"""
        # Common skill patterns
        skill_patterns = [
            r'\b(python|java|javascript|react|angular|vue|django|flask|node\.?js)\b',
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|git)\b',
            r'\b(html|css|typescript|go|rust|php|ruby|swift|kotlin)\b',
            r'\b(machine learning|ml|ai|data science|analytics)\b',
            r'\b(agile|scrum|devops|ci/cd|tdd|rest api|graphql)\b',
        ]
        
        skills = []
        for pattern in skill_patterns:
            matches = re.findall(pattern, self.job_description, re.IGNORECASE)
            skills.extend(matches)
        
        return list(set([s.lower() for s in skills]))
    
    def calculate_keyword_match(self):
        """Calculate keyword matching score"""
        jd_keywords = self._extract_keywords(self.job_description)
        resume_keywords = self._extract_keywords(self.resume_text)
        
        if not jd_keywords:
            return 0, [], [], {}
        
        matched = []
        missing = []
        density = {}
        
        for keyword, jd_count in jd_keywords.items():
            resume_count = resume_keywords.get(keyword, 0)
            
            if resume_count > 0:
                matched.append(keyword)
                density[keyword] = {
                    'jd_count': jd_count,
                    'resume_count': resume_count,
                    'match_ratio': min(resume_count / jd_count, 1.0)
                }
            else:
                missing.append(keyword)
        
        # Calculate match percentage
        match_score = (len(matched) / len(jd_keywords)) * 100 if jd_keywords else 0
        
        return round(match_score), matched[:20], missing[:20], density
    
    def check_required_skills(self):
        """Check if resume contains required technical skills"""
        required_skills = self._extract_required_skills()
        found_skills = []
        missing_skills = []
        
        for skill in required_skills:
            if skill in self.resume_text:
                found_skills.append(skill)
            else:
                missing_skills.append(skill)
        
        if not required_skills:
            return 100, found_skills, missing_skills
        
        skill_score = (len(found_skills) / len(required_skills)) * 100
        return round(skill_score), found_skills, missing_skills
    
    def check_formatting(self):
        """Check ATS-friendly formatting"""
        issues = []
        score = 100
        
        # Check contact information
        if not self.resume.email:
            issues.append("Missing email address")
            score -= 10
        
        if not self.resume.phone:
            issues.append("Missing phone number")
            score -= 5
        
        # Check for clear sections
        if not self.resume.experiences.exists():
            issues.append("No work experience listed")
            score -= 20
        
        if not self.resume.skills.exists():
            issues.append("No skills listed")
            score -= 15
        
        # Check for measurable achievements (numbers in descriptions)
        has_metrics = False
        for exp in self.resume.experiences.all():
            if re.search(r'\d+[%$]?|\d+\+', exp.description):
                has_metrics = True
                break
        
        if not has_metrics:
            issues.append("Add quantifiable achievements (numbers, percentages, metrics)")
            score -= 10
        
        # Check summary length
        if self.resume.summary:
            word_count = len(self.resume.summary.split())
            if word_count < 20:
                issues.append("Professional summary is too short (aim for 50-100 words)")
                score -= 5
            elif word_count > 150:
                issues.append("Professional summary is too long (aim for 50-100 words)")
                score -= 5
        else:
            issues.append("Missing professional summary")
            score -= 10
        
        return max(score, 0), issues
    
    def calculate_readability(self):
        """Simple readability check"""
        if not self.resume_text:
            return 0
        
        sentences = re.split(r'[.!?]+', self.resume_text)
        words = self.resume_text.split()
        
        if not sentences or not words:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Ideal is 15-20 words per sentence for resumes
        if 15 <= avg_sentence_length <= 20:
            return 100
        elif 10 <= avg_sentence_length < 15 or 20 < avg_sentence_length <= 25:
            return 80
        elif avg_sentence_length < 10 or avg_sentence_length > 25:
            return 60
        
        return 70
    
    def generate_suggestions(self, keyword_score, skill_score, format_score, 
                            missing_keywords, missing_skills, format_issues):
        """Generate actionable improvement suggestions"""
        suggestions = []
        
        # Keyword suggestions
        if keyword_score < 60:
            suggestions.append({
                'category': 'Keywords',
                'severity': 'high',
                'message': f'Only {keyword_score}% keyword match. Add more relevant keywords from the job description.',
                'action': f'Focus on these missing keywords: {", ".join(missing_keywords[:5])}'
            })
        elif keyword_score < 80:
            suggestions.append({
                'category': 'Keywords',
                'severity': 'medium',
                'message': 'Good keyword coverage, but room for improvement.',
                'action': f'Consider adding: {", ".join(missing_keywords[:3])}'
            })
        
        # Skill suggestions
        if skill_score < 70 and missing_skills:
            suggestions.append({
                'category': 'Skills',
                'severity': 'high',
                'message': f'Missing {len(missing_skills)} required technical skills.',
                'action': f'Add these skills if you have them: {", ".join(missing_skills[:5])}'
            })
        
        # Formatting suggestions
        for issue in format_issues:
            suggestions.append({
                'category': 'Formatting',
                'severity': 'medium',
                'message': issue,
                'action': 'Update your resume to address this issue.'
            })
        
        # General suggestions
        if not suggestions:
            suggestions.append({
                'category': 'General',
                'severity': 'low',
                'message': 'Your resume looks great! Continue refining based on specific job requirements.',
                'action': 'Review and update before each application.'
            })
        
        return suggestions
    
    def analyze(self):
        """Perform complete ATS analysis"""
        # Calculate individual scores
        keyword_score, matched_kw, missing_kw, density = self.calculate_keyword_match()
        skill_score, found_skills, missing_skills = self.check_required_skills()
        format_score, format_issues = self.check_formatting()
        readability = self.calculate_readability()
        
        # Calculate overall score (weighted average)
        overall_score = round(
            (keyword_score * 0.35) +
            (skill_score * 0.30) +
            (format_score * 0.25) +
            (readability * 0.10)
        )
        
        # Generate suggestions
        suggestions = self.generate_suggestions(
            keyword_score, skill_score, format_score,
            missing_kw, missing_skills, format_issues
        )
        
        # Save analysis
        analysis = ATSAnalysis.objects.create(
            resume=self.resume,
            job_description=self.job_description,
            score=overall_score,
            matched_keywords=matched_kw,
            missing_keywords=missing_kw,
            keyword_density=density,
            suggestions=suggestions,
            has_contact_info=(self.resume.email and self.resume.phone),
            has_clear_sections=(
                self.resume.experiences.exists() and 
                self.resume.skills.exists()
            ),
            has_measurable_achievements=('quantifiable achievements' not in ' '.join(format_issues).lower()),
            readability_score=readability
        )
        
        # Update resume score
        self.resume.ats_score = overall_score
        self.resume.last_ats_check = timezone.now()
        self.resume.save()
        
        return analysis
    
    def get_detailed_report(self):
        """Get detailed analysis report"""
        keyword_score, matched_kw, missing_kw, density = self.calculate_keyword_match()
        skill_score, found_skills, missing_skills = self.check_required_skills()
        format_score, format_issues = self.check_formatting()
        readability = self.calculate_readability()
        
        return {
            'overall_score': round(
                (keyword_score * 0.35) +
                (skill_score * 0.30) +
                (format_score * 0.25) +
                (readability * 0.10)
            ),
            'breakdown': {
                'keyword_match': keyword_score,
                'skill_match': skill_score,
                'formatting': format_score,
                'readability': readability
            },
            'matched_keywords': matched_kw[:10],
            'missing_keywords': missing_kw[:10],
            'found_skills': found_skills,
            'missing_skills': missing_skills,
            'format_issues': format_issues,
            'suggestions': self.generate_suggestions(
                keyword_score, skill_score, format_score,
                missing_kw, missing_skills, format_issues
            )
        }