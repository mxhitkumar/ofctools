from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def generate_resume_pdf(resume):
    """
    Generate a PDF from resume data using WeasyPrint.
    WeasyPrint renders HTML/CSS to PDF with excellent quality.
    
    Args:
        resume: Resume model instance
    
    Returns:
        bytes: PDF file content
    """
    
    # Get the template based on resume's selected template
    template_name = f'resumes/pdf_templates/{resume.template}.html'
    
    # Prepare context data
    context = {
        'resume': resume,
        'experiences': resume.experiences.all().order_by('-start_date'),
        'educations': resume.educations.all().order_by('-start_date'),
        'skills': resume.skills.all(),
        'certifications': resume.certifications.all().order_by('-issue_date'),
        'projects': resume.projects.all().order_by('-start_date'),
    }
    
    # Render HTML
    html_string = render_to_string(template_name, context)
    
    # Create PDF
    font_config = FontConfiguration()
    
    # Custom CSS for PDF (you can also load from file)
    css = CSS(string=get_pdf_styles(), font_config=font_config)
    
    # Generate PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[css], font_config=font_config)
    
    return pdf


def get_pdf_styles():
    """
    Return CSS styles optimized for PDF generation.
    These styles ensure consistent rendering across PDF viewers.
    """
    return """
        @page {
            size: A4;
            margin: 0.75in;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
        }
        
        h1 {
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 8pt;
            color: #2c3e50;
        }
        
        h2 {
            font-size: 14pt;
            font-weight: bold;
            margin-top: 16pt;
            margin-bottom: 8pt;
            padding-bottom: 4pt;
            border-bottom: 2pt solid #3498db;
            color: #2c3e50;
        }
        
        h3 {
            font-size: 12pt;
            font-weight: bold;
            margin-bottom: 4pt;
            color: #34495e;
        }
        
        p {
            margin-bottom: 8pt;
        }
        
        ul {
            margin-left: 18pt;
            margin-bottom: 8pt;
        }
        
        li {
            margin-bottom: 4pt;
        }
        
        .header {
            text-align: center;
            margin-bottom: 20pt;
        }
        
        .contact-info {
            text-align: center;
            font-size: 10pt;
            margin-bottom: 16pt;
            color: #555;
        }
        
        .contact-info a {
            color: #3498db;
            text-decoration: none;
        }
        
        .section {
            margin-bottom: 16pt;
        }
        
        .experience-item,
        .education-item,
        .project-item {
            margin-bottom: 12pt;
            page-break-inside: avoid;
        }
        
        .job-header,
        .edu-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4pt;
        }
        
        .company,
        .institution {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .position,
        .degree {
            font-style: italic;
            color: #555;
        }
        
        .date {
            color: #7f8c8d;
            font-size: 10pt;
        }
        
        .skills-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8pt;
        }
        
        .skill-item {
            padding: 4pt 8pt;
            background-color: #ecf0f1;
            border-radius: 3pt;
            font-size: 10pt;
        }
        
        .skill-name {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .skill-level {
            color: #7f8c8d;
            font-size: 9pt;
        }
        
        /* Ensure links work in PDF */
        a {
            color: #3498db;
        }
        
        /* Page break control */
        .avoid-break {
            page-break-inside: avoid;
        }
    """


def generate_resume_pdf_reportlab(resume):
    """
    Alternative PDF generator using ReportLab.
    ReportLab offers more control but requires more code.
    Use this if you need complex layouts or charts.
    """
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        borderWidth=2,
        borderColor=colors.HexColor('#3498db'),
        borderPadding=4
    )
    
    body_style = styles['BodyText']
    
    # Add name
    elements.append(Paragraph(resume.full_name, title_style))
    
    # Add contact info
    contact_parts = [resume.email]
    if resume.phone:
        contact_parts.append(resume.phone)
    if resume.location:
        contact_parts.append(resume.location)
    
    contact_text = " | ".join(contact_parts)
    contact_style = ParagraphStyle(
        'Contact',
        parent=body_style,
        alignment=TA_CENTER,
        fontSize=10
    )
    elements.append(Paragraph(contact_text, contact_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add summary
    if resume.summary:
        elements.append(Paragraph("Professional Summary", heading_style))
        elements.append(Paragraph(resume.summary, body_style))
        elements.append(Spacer(1, 0.15*inch))
    
    # Add experience
    if resume.experiences.exists():
        elements.append(Paragraph("Work Experience", heading_style))
        
        for exp in resume.experiences.all().order_by('-start_date'):
            # Company and position
            exp_header = f"<b>{exp.company}</b> | {exp.position}"
            elements.append(Paragraph(exp_header, body_style))
            
            # Dates
            date_text = f"{exp.start_date.strftime('%b %Y')} - "
            date_text += "Present" if exp.is_current else exp.end_date.strftime('%b %Y')
            elements.append(Paragraph(date_text, body_style))
            
            # Description
            elements.append(Paragraph(exp.description, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.1*inch))
    
    # Add skills
    if resume.skills.exists():
        elements.append(Paragraph("Skills", heading_style))
        
        skills_by_category = {}
        for skill in resume.skills.all():
            category = skill.get_category_display()
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill.name)
        
        for category, skills in skills_by_category.items():
            skills_text = f"<b>{category}:</b> {', '.join(skills)}"
            elements.append(Paragraph(skills_text, body_style))
        
        elements.append(Spacer(1, 0.15*inch))
    
    # Add education
    if resume.educations.exists():
        elements.append(Paragraph("Education", heading_style))
        
        for edu in resume.educations.all().order_by('-start_date'):
            edu_text = f"<b>{edu.institution}</b> | {edu.get_degree_display()} in {edu.field_of_study}"
            elements.append(Paragraph(edu_text, body_style))
            
            date_text = f"{edu.start_date.strftime('%Y')} - {edu.end_date.strftime('%Y') if edu.end_date else 'Present'}"
            if edu.gpa:
                date_text += f" | GPA: {edu.gpa}"
            elements.append(Paragraph(date_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf