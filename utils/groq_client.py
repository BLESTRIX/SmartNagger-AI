import os
from groq import Groq
import streamlit as st

class GroqComplaintGenerator:
    def __init__(self):
        """Initialize Groq client"""
        try:
            # Get API key from secrets or environment
            api_key = os.getenv("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
            
            if not api_key:
                st.warning("⚠️ Groq API key not configured. Using template complaints.")
                self.client = None
            else:
                self.client = Groq(api_key=api_key)
        except Exception as e:
            st.warning(f"⚠️ Could not initialize Groq: {str(e)}")
            self.client = None
    
    def generate_formal_complaint(self, issue_data, language="english"):
        """
        Generate formal complaint using Groq AI
        
        Args:
            issue_data: dict with keys: issue_type, severity, location, district, 
                       description, department
            language: "english" or "urdu"
        
        Returns:
            Formatted complaint text
        """
        if not self.client:
            return self._generate_template_complaint(issue_data, language)
        
        try:
            # Create prompt based on language
            if language.lower() == "urdu":
                prompt = self._create_urdu_prompt(issue_data)
            else:
                prompt = self._create_english_prompt(issue_data)
            
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(language)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",  # Fast and good quality
                temperature=0.3,  # More formal and consistent
                max_tokens=1000
            )
            
            complaint_text = chat_completion.choices[0].message.content
            return complaint_text
            
        except Exception as e:
            st.error(f"Error generating complaint: {str(e)}")
            return self._generate_template_complaint(issue_data, language)
    
    def _get_system_prompt(self, language):
        """Get system prompt for Groq"""
        if language.lower() == "urdu":
            return """You are a professional complaint writer for Pakistani civic authorities. 
Write formal complaints in proper Urdu (اردو) with correct grammar and respectful tone.
Use formal Urdu language suitable for government correspondence.
Format the complaint professionally with proper structure."""
        else:
            return """You are a professional complaint writer for civic authorities in Pakistan.
Write formal, professional complaints suitable for government departments.
Use respectful, formal English with proper structure and grammar.
Be clear, concise, and actionable."""
    
    def _create_english_prompt(self, issue_data):
        """Create English prompt for Groq"""
        return f"""Write a formal civic complaint letter with the following details:

Issue Type: {issue_data['issue_type']}
Severity: {issue_data['severity']}
Location: {issue_data['location']}, {issue_data['district']}
Department: {issue_data['department']}
Citizen Description: {issue_data['description']}

Structure the complaint as:
1. Subject line
2. Respectful greeting to the department
3. Clear description of the issue
4. Location details
5. Impact/urgency based on severity
6. Request for action
7. Professional closing

Make it formal, respectful, and actionable. Keep it concise (200-300 words).
Do NOT include sender name/address or date - only the complaint body."""
    
    def _create_urdu_prompt(self, issue_data):
        """Create Urdu prompt for Groq"""
        return f"""ایک رسمی شہری شکایت لکھیں جس میں یہ تفصیلات ہوں:

مسئلے کی قسم: {issue_data['issue_type']}
شدت: {issue_data['severity']}
مقام: {issue_data['location']}, {issue_data['district']}
محکمہ: {issue_data['department']}
شہری کی تفصیل: {issue_data['description']}

شکایت میں یہ شامل کریں:
1. موضوع
2. محترم محکمہ کو سلام
3. مسئلے کی واضح تفصیل
4. مقام کی تفصیلات
5. شدت کی بنیاد پر اثر
6. کارروائی کی درخواست
7. رسمی اختتام

شکایت رسمی، مہذب اور قابل عمل ہو۔ مختصر رکھیں (200-300 الفاظ)۔
بھیجنے والے کا نام/پتہ یا تاریخ شامل نہ کریں - صرف شکایت کا متن۔"""
    
    def _generate_template_complaint(self, issue_data, language):
        """Fallback template if Groq unavailable"""
        if language.lower() == "urdu":
            return f"""موضوع: {issue_data['issue_type']} کی شکایت - {issue_data['location']}

محترم {issue_data['department']}،

السلام علیکم،

میں آپ کی توجہ {issue_data['location']}, {issue_data['district']} میں {issue_data['issue_type']} کی طرف مبذول کرانا چاہتا ہوں۔

مسئلے کی تفصیل:
{issue_data['description']}

یہ مسئلہ {issue_data['severity']} نوعیت کا ہے اور فوری توجہ کا متقاضی ہے۔ یہ مسئلہ عوام کو پریشانی کا باعث بن رہا ہے۔

درخواست ہے کہ اس مسئلے کو جلد از جلد حل کیا جائے۔

شکریہ
شہری"""
        else:
            return f"""Subject: Complaint Regarding {issue_data['issue_type']} at {issue_data['location']}

Dear Sir/Madam,
{issue_data['department']}

I am writing to bring to your attention a {issue_data['severity'].lower()} severity civic issue at {issue_data['location']}, {issue_data['district']}.

Issue Description:
{issue_data['description']}

This is a {issue_data['issue_type']} issue that requires immediate attention. It is causing significant inconvenience to the public and poses safety concerns.

Given the {issue_data['severity'].lower()} severity of this matter, I request that your department take prompt action to resolve this issue at the earliest.

I appreciate your attention to this matter and look forward to a swift resolution.

Thank you for your service to the community.

Respectfully,
Concerned Citizen"""

# Initialize Groq generator
@st.cache_resource
def get_groq_generator():
    return GroqComplaintGenerator()