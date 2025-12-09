"""
PDF Report Generator for Due Diligence Reports.

Converts JSON reports from synthesis node into professionally formatted PDF documents.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, ListFlowable, ListItem
)
from reportlab.pdfgen import canvas


class PDFReportGenerator:
    """Generate professional PDF reports from JSON due diligence data."""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize PDF generator.
        
        Args:
            output_dir: Directory to save PDF files (defaults to reports/)
        """
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        
        # Helper to add or override styles
        def add_style(style):
            if style.name in self.styles:
                del self.styles[style.name]
            self.styles.add(style)
        
        # Title style
        add_style(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header
        add_style(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5,
            backColor=colors.HexColor('#ecf0f1')
        ))
        
        # Subsection header
        add_style(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body text
        add_style(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Executive summary
        add_style(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=15,
            alignment=TA_JUSTIFY,
            leading=16,
            backColor=colors.HexColor('#fff3cd'),
            borderWidth=1,
            borderColor=colors.HexColor('#ffc107'),
            borderPadding=10
        ))
        
        # Risk level styles
        self.risk_colors = {
            'CRITICAL': colors.HexColor('#dc3545'),
            'HIGH': colors.HexColor('#fd7e14'),
            'MEDIUM': colors.HexColor('#ffc107'),
            'LOW': colors.HexColor('#28a745')
        }
    
    def _create_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page."""
        canvas_obj.saveState()
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(
            inch,
            0.5 * inch,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        canvas_obj.drawRightString(
            doc.width + inch,
            0.5 * inch,
            f"Page {doc.page}"
        )
        
        canvas_obj.restoreState()
    
    def _add_cover_page(self, report_data: Dict[str, Any], story: List):
        """Add cover page to the report."""
        # Title
        story.append(Spacer(1, 2.5*inch))
        story.append(Paragraph("DUE DILIGENCE REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.8*inch))
        
        # Subject
        metadata = report_data.get('metadata', {})
        subject = metadata.get('subject', 'Unknown Subject')
        story.append(Paragraph(
            f"<b>Subject:</b> {subject}",
            self.styles['Heading2']
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # Risk level with color coding
        risk_level = report_data.get('risk_level', 'UNKNOWN')
        risk_color = self.risk_colors.get(risk_level, colors.grey)
        story.append(Paragraph(
            f"<b>Risk Level:</b> <font color='{risk_color.hexval()}'><b>{risk_level}</b></font>",
            self.styles['Heading2']
        ))
        
        # Confidentiality notice
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(
            "<b>CONFIDENTIAL</b><br/>"
            "This report contains sensitive information and is intended solely for authorized recipients. "
            "Unauthorized distribution or disclosure is prohibited.",
            ParagraphStyle(
                'Notice',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.red,
                alignment=TA_CENTER
            )
        ))
        
        story.append(PageBreak())
    
    def _add_executive_summary(self, report_data: Dict[str, Any], story: List):
        """Add executive summary section."""
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        exec_summary = report_data.get('executive_summary', 'No executive summary available.')
        story.append(Paragraph(exec_summary, self.styles['ExecutiveSummary']))
        story.append(Spacer(1, 0.3*inch))
    
    def _add_key_findings(self, report_data: Dict[str, Any], story: List):
        """Add key findings section."""
        story.append(Paragraph("KEY FINDINGS", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        findings = report_data.get('key_findings', [])
        if findings:
            for i, finding in enumerate(findings, 1):
                # Color code based on severity tags
                if '[CRITICAL]' in finding:
                    color = self.risk_colors['CRITICAL'].hexval()
                elif '[HIGH]' in finding:
                    color = self.risk_colors['HIGH'].hexval()
                elif '[MEDIUM]' in finding:
                    color = self.risk_colors['MEDIUM'].hexval()
                else:
                    color = '#2c3e50'
                
                story.append(Paragraph(
                    f"<font color='{color}'><b>{i}.</b> {finding}</font>",
                    self.styles['ReportBody']
                ))
        else:
            story.append(Paragraph("No key findings recorded.", self.styles['ReportBody']))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_text_section(self, title: str, content: str, story: List):
        """Add a standard text section."""
        story.append(Paragraph(title.upper(), self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        if content:
            # Handle multi-paragraph content
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['ReportBody']))
        else:
            story.append(Paragraph(f"No {title.lower()} available.", self.styles['ReportBody']))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_red_flags(self, report_data: Dict[str, Any], story: List):
        """Add red flags section with severity color coding."""
        story.append(Paragraph("RED FLAGS", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        red_flags = report_data.get('red_flags', [])
        if red_flags:
            for flag in red_flags:
                severity = flag.get('severity', 'UNKNOWN')
                detail = flag.get('detail', 'No detail provided')
                color = self.risk_colors.get(severity, colors.grey).hexval()
                
                story.append(Paragraph(
                    f"<font color='{color}'><b>[{severity}]</b></font> {detail}",
                    self.styles['ReportBody']
                ))
        else:
            story.append(Paragraph("No red flags identified.", self.styles['ReportBody']))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_list_section(self, title: str, items: List[str], story: List):
        """Add a bulleted list section."""
        story.append(Paragraph(title.upper(), self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        if items:
            for item in items:
                story.append(Paragraph(f"• {item}", self.styles['ReportBody']))
        else:
            story.append(Paragraph(f"No {title.lower()} recorded.", self.styles['ReportBody']))
        
        story.append(Spacer(1, 0.2*inch))
    
    def _add_entity_graph_summary(self, report_data: Dict[str, Any], story: List):
        """Add entity graph summary."""
        story.append(Paragraph("ENTITY NETWORK ANALYSIS", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        entity_graph = report_data.get('entity_graph', {})
        nodes = entity_graph.get('nodes', [])
        edges = entity_graph.get('edges', [])
        
        # Summary statistics
        story.append(Paragraph(
            f"<b>Total Entities:</b> {len(nodes)} | <b>Total Relationships:</b> {len(edges)}",
            self.styles['SubsectionHeader']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # Key entities
        if nodes:
            story.append(Paragraph("<b>Key Entities:</b>", self.styles['SubsectionHeader']))
            for node in nodes[:15]:  # Show top 15
                name = node.get('name', 'Unknown')
                entity_type = node.get('type', 'Unknown')
                story.append(Paragraph(
                    f"• <b>{name}</b> ({entity_type})",
                    self.styles['ReportBody']
                ))
            
            if len(nodes) > 15:
                story.append(Paragraph(
                    f"<i>... and {len(nodes) - 15} more entities</i>",
                    self.styles['ReportBody']
                ))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Key relationships
        if edges:
            story.append(Paragraph("<b>Key Relationships:</b>", self.styles['SubsectionHeader']))
            for edge in edges[:20]:  # Show top 20
                source = edge.get('source', '?').replace('_', ' ').title()
                target = edge.get('target', '?').replace('_', ' ').title()
                relationship = edge.get('relationship', '?').replace('_', ' ')
                
                story.append(Paragraph(
                    f"• {source} → <i>{relationship}</i> → {target}",
                    self.styles['ReportBody']
                ))
            
            if len(edges) > 20:
                story.append(Paragraph(
                    f"<i>... and {len(edges) - 20} more relationships</i>",
                    self.styles['ReportBody']
                ))
        
        story.append(Spacer(1, 0.2*inch))
    
    def generate_pdf(self, json_path: Path) -> Path:
        """
        Generate PDF report from JSON file.
        
        Args:
            json_path: Path to JSON report file
            
        Returns:
            Path to generated PDF file
        """
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Setup PDF
        pdf_filename = json_path.stem + '.pdf'
        pdf_path = self.output_dir / pdf_filename
        
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build story (content)
        story = []
        
        # Cover page
        self._add_cover_page(report_data, story)
        
        # Executive summary
        self._add_executive_summary(report_data, story)
        
        # Key findings
        self._add_key_findings(report_data, story)
        
        # Biographical overview
        self._add_text_section(
            "Biographical Overview",
            report_data.get('biographical_overview', ''),
            story
        )
        
        # Professional history
        self._add_text_section(
            "Professional History",
            report_data.get('professional_history', ''),
            story
        )
        
        # Financial analysis
        self._add_text_section(
            "Financial Analysis",
            report_data.get('financial_analysis', ''),
            story
        )
        
        # Legal & regulatory
        self._add_text_section(
            "Legal & Regulatory Exposure",
            report_data.get('legal_regulatory', ''),
            story
        )
        
        # Behavioral patterns
        self._add_text_section(
            "Behavioral Patterns",
            report_data.get('behavioral_patterns', ''),
            story
        )
        
        # Red flags
        self._add_red_flags(report_data, story)
        
        # Neutral facts
        self._add_list_section(
            "Neutral Facts",
            report_data.get('neutral_facts', []),
            story
        )
        
        # Positive indicators
        self._add_list_section(
            "Positive Indicators",
            report_data.get('positive_indicators', []),
            story
        )
        
        # Key relationships
        self._add_list_section(
            "Key Relationships",
            report_data.get('key_relationships', []),
            story
        )
        
        # Suspicious connections
        self._add_list_section(
            "Suspicious Connections",
            report_data.get('suspicious_connections', []),
            story
        )
        
        # Entity graph
        self._add_entity_graph_summary(report_data, story)
        
        # Source assessment
        self._add_text_section(
            "Source Assessment",
            report_data.get('source_summary', ''),
            story
        )
        
        # Evidence strength
        self._add_text_section(
            "Evidence Strength",
            report_data.get('evidence_strength', ''),
            story
        )
        
        # Information gaps
        self._add_list_section(
            "Information Gaps",
            report_data.get('information_gaps', []),
            story
        )
        
        # Research limitations
        self._add_text_section(
            "Research Limitations",
            report_data.get('research_limitations', ''),
            story
        )
        
        # Recommendations
        self._add_list_section(
            "Recommendations",
            report_data.get('recommendations', []),
            story
        )
        
        # Build PDF
        doc.build(story, onFirstPage=self._create_header_footer, onLaterPages=self._create_header_footer)
        
        return pdf_path
    
    def convert_all_reports(self, reports_dir: Path = None) -> List[Path]:
        """
        Convert all JSON reports in a directory to PDF.
        
        Args:
            reports_dir: Directory containing JSON reports (defaults to reports/)
            
        Returns:
            List of paths to generated PDF files
        """
        if reports_dir is None:
            reports_dir = Path("reports")
        
        json_files = list(reports_dir.glob("*_report.json"))
        pdf_paths = []
        
        print(f"\nFound {len(json_files)} JSON report(s) to convert...")
        
        for json_file in json_files:
            try:
                print(f"\nConverting: {json_file.name}")
                pdf_path = self.generate_pdf(json_file)
                pdf_paths.append(pdf_path)
                print(f"✓ Generated: {pdf_path.name}")
            except Exception as e:
                print(f"✗ Error converting {json_file.name}: {e}")
        
        return pdf_paths


def main():
    """CLI interface for PDF generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Due Diligence JSON reports to PDF")
    parser.add_argument(
        '--input',
        type=Path,
        help='Path to specific JSON file to convert'
    )
    parser.add_argument(
        '--reports-dir',
        type=Path,
        default=Path('reports'),
        help='Directory containing JSON reports (default: reports/)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory for PDFs (default: same as reports-dir)'
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir or args.reports_dir
    generator = PDFReportGenerator(output_dir=output_dir)
    
    if args.input:
        # Convert single file
        pdf_path = generator.generate_pdf(args.input)
        print(f"\n✓ PDF generated: {pdf_path}")
    else:
        # Convert all reports
        pdf_paths = generator.convert_all_reports(args.reports_dir)
        print(f"\n✓ Successfully generated {len(pdf_paths)} PDF report(s)")
        print(f"✓ Location: {output_dir.absolute()}")


if __name__ == '__main__':
    main()

