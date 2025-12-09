#!/usr/bin/env python3
"""
Convenient script to convert JSON reports to PDFs.

By default, this script will process ALL JSON reports in the reports/ folder
and save the PDFs alongside the JSON files.

Usage:
    python convert_to_pdf.py                    # Convert all reports (default)
    python convert_to_pdf.py --session <id>     # Convert specific session
    python convert_to_pdf.py --latest           # Convert latest report only
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.pdf_generator import PDFReportGenerator


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert Due Diligence JSON reports to PDF (processes all reports by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_to_pdf.py                           # Convert all JSON reports to PDF (default)
  python convert_to_pdf.py --session sess_20251208   # Convert specific session
  python convert_to_pdf.py --latest                  # Convert only the latest report
        """
    )
    
    parser.add_argument(
        '--session',
        type=str,
        help='Convert specific session report (e.g., sess_20251208_212522)'
    )
    parser.add_argument(
        '--latest',
        action='store_true',
        help='Convert only the latest report'
    )
    parser.add_argument(
        '--reports-dir',
        type=Path,
        default=Path('reports'),
        help='Directory containing JSON reports (default: reports/)'
    )
    
    args = parser.parse_args()
    
    # Setup - always save PDFs in the same directory as JSON reports
    reports_dir = args.reports_dir
    
    if not reports_dir.exists():
        print(f"Error: Reports directory not found: {reports_dir}")
        sys.exit(1)
    
    # Output PDFs to the same directory as the JSON files
    generator = PDFReportGenerator(output_dir=reports_dir)
    
    # Determine which files to convert
    if args.session:
        # Convert specific session
        json_files = list(reports_dir.glob(f"{args.session}*_report.json"))
        if not json_files:
            print(f"Error: No report found for session: {args.session}")
            sys.exit(1)
        json_file = json_files[0]
        
        print(f"\nConverting session: {args.session}")
        pdf_path = generator.generate_pdf(json_file)
        print(f"✓ PDF generated: {pdf_path}")
        
    elif args.latest:
        # Convert latest report only
        json_files = sorted(reports_dir.glob("*_report.json"), key=lambda p: p.stat().st_mtime)
        if not json_files:
            print("Error: No reports found")
            sys.exit(1)
        
        json_file = json_files[-1]
        print(f"\nConverting latest report: {json_file.name}")
        pdf_path = generator.generate_pdf(json_file)
        print(f"✓ PDF generated: {pdf_path}")
        
    else:
        # DEFAULT: Convert all reports in the directory
        print(f"\nProcessing all reports in: {reports_dir.absolute()}")
        pdf_paths = generator.convert_all_reports(reports_dir)
        
        if pdf_paths:
            print(f"\n{'='*60}")
            print(f"✓ Successfully generated {len(pdf_paths)} PDF report(s)")
            print(f"✓ Location: {reports_dir.absolute()}")
            print(f"{'='*60}")
            print("\nGenerated PDFs:")
            for pdf_path in pdf_paths:
                print(f"  • {pdf_path.name}")
        else:
            print("\n⚠ No reports were converted (no JSON files found).")


if __name__ == '__main__':
    main()

