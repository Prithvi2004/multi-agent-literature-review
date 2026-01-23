# export_manager.py
"""
Export Manager Module for Multi-Agent Literature Review System
Handles exporting analysis results to various formats: PDF, LaTeX, Markdown, BibTeX
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

# Try importing optional dependencies
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed. PDF export will not be available.")

def generate_markdown(analysis_data: Dict[str, Any]) -> str:
    """
    Generate Markdown format export.
    
    Args:
        analysis_data: Dictionary containing analysis results
        
    Returns:
        Markdown formatted string
    """
    md = []
    
    # Header
    md.append(f"# Literature Review Analysis Report")
    md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Research Idea
    if 'research_idea' in analysis_data:
        md.append(f"## Research Idea\n")
        md.append(f"{analysis_data['research_idea']}\n")
    
    # Domains
    if 'domains' in analysis_data and analysis_data['domains']:
        md.append(f"## Research Domains\n")
        for domain in analysis_data['domains']:
            md.append(f"- {domain}")
        md.append("")
    
    # Metrics
    if 'metrics' in analysis_data:
        metrics = analysis_data['metrics']
        md.append(f"## Analysis Metrics\n")
        md.append(f"| Metric | Value |")
        md.append(f"|--------|-------|")
        if 'total_papers_retrieved' in metrics:
            md.append(f"| Papers Retrieved | {metrics['total_papers_retrieved']} |")
        if 'total_duration_seconds' in metrics:
            md.append(f"| Analysis Duration | {metrics['total_duration_seconds']:.2f}s |")
        if 'total_agents' in metrics:
            md.append(f"| Agents Used | {metrics['total_agents']} |")
        md.append("")
    
    # Final Report
    if 'final_report' in analysis_data:
        md.append(f"## Final Report\n")
        md.append(analysis_data['final_report'])
        md.append("")
    
    # Retrieved Papers
    if 'papers' in analysis_data and analysis_data['papers']:
        md.append(f"## Retrieved Papers\n")
        for i, paper in enumerate(analysis_data['papers'], 1):
            md.append(f"### [{paper.get('handle', f'P{i}')}] {paper.get('title', 'Untitled')}\n")
            md.append(f"**Authors:** {paper.get('authors', 'Unknown')}")
            md.append(f"**Year:** {paper.get('year', 'N/A')}\n")
            if paper.get('abstract'):
                md.append(f"**Abstract:** {paper['abstract']}\n")
    
    return "\n".join(md)

def generate_latex(analysis_data: Dict[str, Any]) -> str:
    """
    Generate LaTeX format export.
    
    Args:
        analysis_data: Dictionary containing analysis results
        
    Returns:
        LaTeX formatted string
    """
    latex = []
    
    # Document class and packages
    latex.append(r"\documentclass[11pt,a4paper]{article}")
    latex.append(r"\usepackage[utf8]{inputenc}")
    latex.append(r"\usepackage[margin=1in]{geometry}")
    latex.append(r"\usepackage{hyperref}")
    latex.append(r"\usepackage{graphicx}")
    latex.append(r"\usepackage{booktabs}")
    latex.append(r"")
    latex.append(r"\title{Literature Review Analysis Report}")
    latex.append(r"\author{Multi-Agent Literature Review System}")
    latex.append(r"\date{" + datetime.now().strftime('%Y-%m-%d') + r"}")
    latex.append(r"")
    latex.append(r"\begin{document}")
    latex.append(r"\maketitle")
    latex.append(r"")
    
    # Research Idea
    if 'research_idea' in analysis_data:
        latex.append(r"\section{Research Idea}")
        latex.append(escape_latex(analysis_data['research_idea']))
        latex.append(r"")
    
    # Domains
    if 'domains' in analysis_data and analysis_data['domains']:
        latex.append(r"\section{Research Domains}")
        latex.append(r"\begin{itemize}")
        for domain in analysis_data['domains']:
            latex.append(r"\item " + escape_latex(domain))
        latex.append(r"\end{itemize}")
        latex.append(r"")
    
    # Final Report
    if 'final_report' in analysis_data:
        latex.append(r"\section{Final Report}")
        latex.append(escape_latex(analysis_data['final_report']))
        latex.append(r"")
    
    # Retrieved Papers
    if 'papers' in analysis_data and analysis_data['papers']:
        latex.append(r"\section{Retrieved Papers}")
        for i, paper in enumerate(analysis_data['papers'], 1):
            latex.append(r"\subsection{" + escape_latex(paper.get('title', 'Untitled')) + r"}")
            latex.append(r"\textbf{Authors:} " + escape_latex(paper.get('authors', 'Unknown')) + r"\\")
            latex.append(r"\textbf{Year:} " + str(paper.get('year', 'N/A')) + r"\\")
            if paper.get('abstract'):
                latex.append(r"\textbf{Abstract:} " + escape_latex(paper['abstract']))
            latex.append(r"")
    
    latex.append(r"\end{document}")
    
    return "\n".join(latex)

def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_bibtex(papers: List[Dict[str, Any]]) -> str:
    """
    Generate BibTeX format for retrieved papers.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        BibTeX formatted string
    """
    bibtex = []
    
    for i, paper in enumerate(papers, 1):
        # Generate citation key
        authors = paper.get('authors', 'Unknown').split(',')[0].split()
        first_author = authors[-1] if authors else 'Unknown'
        year = paper.get('year', 'XXXX')
        key = f"{first_author}{year}_{i}"
        
        bibtex.append(f"@article{{{key},")
        bibtex.append(f"  title={{{paper.get('title', 'Untitled')}}},")
        bibtex.append(f"  author={{{paper.get('authors', 'Unknown')}}},")
        bibtex.append(f"  year={{{year}}},")
        if paper.get('abstract'):
            bibtex.append(f"  abstract={{{paper['abstract']}}},")
        if paper.get('url'):
            bibtex.append(f"  url={{{paper['url']}}},")
        bibtex.append(f"  note={{Retrieved from {paper.get('source', 'Unknown source')}}}")
        bibtex.append("}\n")
    
    return "\n".join(bibtex)

def generate_pdf(analysis_data: Dict[str, Any]) -> Optional[bytes]:
    """
    Generate PDF format export using ReportLab.
    
    Args:
        analysis_data: Dictionary containing analysis results
        
    Returns:
        PDF file as bytes, or None if ReportLab not available
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("ReportLab not available for PDF generation")
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
    )
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Title
    elements.append(Paragraph("Literature Review Analysis Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Research Idea
    if 'research_idea' in analysis_data:
        elements.append(Paragraph("Research Idea", heading_style))
        elements.append(Paragraph(analysis_data['research_idea'], normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Domains
    if 'domains' in analysis_data and analysis_data['domains']:
        elements.append(Paragraph("Research Domains", heading_style))
        for domain in analysis_data['domains']:
            elements.append(Paragraph(f"• {domain}", normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Metrics
    if 'metrics' in analysis_data:
        elements.append(Paragraph("Analysis Metrics", heading_style))
        metrics = analysis_data['metrics']
        data = []
        if 'total_papers_retrieved' in metrics:
            data.append(['Papers Retrieved', str(metrics['total_papers_retrieved'])])
        if 'total_duration_seconds' in metrics:
            data.append(['Analysis Duration', f"{metrics['total_duration_seconds']:.2f}s"])
        if 'total_agents' in metrics:
            data.append(['Agents Used', str(metrics['total_agents'])])
        
        if data:
            table = Table(data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
    
    # Final Report
    if 'final_report' in analysis_data:
        elements.append(PageBreak())
        elements.append(Paragraph("Final Report", heading_style))
        # Split report into paragraphs
        for para in analysis_data['final_report'].split('\n\n'):
            if para.strip():
                elements.append(Paragraph(para, normal_style))
                elements.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def export_analysis(analysis_data: Dict[str, Any], format: str = 'markdown') -> tuple[bytes, str, str]:
    """
    Export analysis to specified format.
    
    Args:
        analysis_data: Dictionary containing analysis results
        format: Export format ('markdown', 'latex', 'bibtex', 'pdf')
        
    Returns:
        Tuple of (content_bytes, filename, mimetype)
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format == 'markdown':
        content = generate_markdown(analysis_data)
        return content.encode('utf-8'), f'analysis_report_{timestamp}.md', 'text/markdown'
    
    elif format == 'latex':
        content = generate_latex(analysis_data)
        return content.encode('utf-8'), f'analysis_report_{timestamp}.tex', 'application/x-latex'
    
    elif format == 'bibtex':
        papers = analysis_data.get('papers', [])
        content = generate_bibtex(papers)
        return content.encode('utf-8'), f'references_{timestamp}.bib', 'application/x-bibtex'
    
    elif format == 'pdf':
        pdf_bytes = generate_pdf(analysis_data)
        if pdf_bytes:
            return pdf_bytes, f'analysis_report_{timestamp}.pdf', 'application/pdf'
        else:
            raise ValueError("PDF generation not available (ReportLab not installed)")
    
    else:
        raise ValueError(f"Unsupported export format: {format}")
