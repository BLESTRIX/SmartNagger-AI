from fpdf import FPDF
from io import BytesIO
from PIL import Image
import tempfile
from datetime import datetime

class ComplaintPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """PDF Header"""
        self.set_font('Arial', 'B', 20)
        self.set_text_color(41, 128, 185)
        self.cell(0, 10, 'SmartNaggar AI', ln=True, align='C')
        self.set_font('Arial', '', 12)
        self.set_text_color(127, 140, 141)
        self.cell(0, 5, 'Civic Problem Reporter', ln=True, align='C')
        self.ln(5)
        self.set_draw_color(41, 128, 185)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        """PDF Footer"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(127, 140, 141)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Page {self.page_no()}', 0, 0, 'C')
    
    def add_section_title(self, title):
        """Add section title"""
        self.set_font('Arial', 'B', 14)
        self.set_text_color(52, 73, 94)
        self.cell(0, 10, title, ln=True)
        self.ln(2)
    
    def add_field(self, label, value):
        """Add field with label and value"""
        self.set_font('Arial', 'B', 11)
        self.set_text_color(44, 62, 80)
        self.cell(50, 8, f'{label}:', 0)
        self.set_font('Arial', '', 11)
        self.set_text_color(52, 73, 94)
        self.multi_cell(0, 8, str(value))
        self.ln(2)

def generate_complaint_pdf(complaint_data, image_file=None):
    """
    Generate enhanced complaint PDF
    
    Args:
        complaint_data: dict with keys: tracking_id, issue_type, severity, 
                       department, location, district, description, status, created_at
        image_file: uploaded image file (optional)
    
    Returns:
        BytesIO object containing PDF
    """
    pdf = ComplaintPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(231, 76, 60)
    pdf.cell(0, 10, 'CIVIC COMPLAINT REPORT', ln=True, align='C')
    pdf.ln(5)
    
    # Tracking ID (Prominent)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, f"Tracking ID: {complaint_data.get('tracking_id', 'N/A')}", ln=True, align='C', fill=True)
    pdf.ln(8)
    
    # Issue Details Section
    pdf.add_section_title('Issue Details')
    pdf.add_field('Issue Type', complaint_data.get('issue_type', 'N/A'))
    pdf.add_field('Severity', complaint_data.get('severity', 'N/A'))
    pdf.add_field('Assigned Department', complaint_data.get('department', 'N/A'))
    pdf.add_field('Status', complaint_data.get('status', 'Pending'))
    pdf.ln(3)
    
    # Location Details Section
    pdf.add_section_title('Location Details')
    pdf.add_field('District/City', complaint_data.get('district', 'N/A'))
    pdf.add_field('Exact Location', complaint_data.get('location', 'N/A'))
    pdf.ln(3)
    
    # Complaint Description Section
    pdf.add_section_title('Complaint Description')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(52, 73, 94)
    description = complaint_data.get('description', 'No description provided')
    pdf.multi_cell(0, 8, description)
    pdf.ln(5)
    
    # Image Evidence (if provided)
    if image_file:
        pdf.add_section_title('Photo Evidence')
        try:
            image = Image.open(image_file)
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_file.name)
            
            # Add image to PDF (resize to fit)
            pdf.image(temp_file.name, x=15, w=180)
            pdf.ln(5)
        except Exception as e:
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(231, 76, 60)
            pdf.cell(0, 8, 'Error loading image evidence', ln=True)
            pdf.ln(3)
    
    # Submission Info
    pdf.add_section_title('Submission Information')
    pdf.add_field('Submitted On', complaint_data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    pdf.ln(5)
    
    # Instructions Box
    pdf.set_fill_color(236, 240, 241)
    pdf.set_draw_color(189, 195, 199)
    pdf.rect(10, pdf.get_y(), 190, 30, 'DF')
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 8, 'Important Instructions:', ln=True)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(52, 73, 94)
    pdf.multi_cell(0, 5, 
        '1. Keep this Tracking ID for future reference\n'
        '2. You will receive updates via email/SMS\n'
        '3. Check the tracking dashboard for real-time status\n'
        '4. For urgent issues, contact the assigned department directly'
    )
    pdf.ln(5)
    
    # Contact Information
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 5, 'For queries, visit: www.smartnaggar.ai | Email: support@smartnaggar.ai', ln=True, align='C')
    
    # Convert to BytesIO
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)