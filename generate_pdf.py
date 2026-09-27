import markdown
from fpdf import FPDF, HTMLMixin

class PDF(FPDF, HTMLMixin):
    pass

with open('project_report.md', 'r', encoding='utf-8') as f:
    text = f.read()

html = markdown.markdown(text)

pdf = PDF()
pdf.add_page()
pdf.write_html(html)
pdf.output('TruthScan_Project_Report.pdf')
