import os
from supabase import create_client, Client
from datetime import datetime
import streamlit as st

# Initialize Supabase client
def get_supabase_client() -> Client:
    """Initialize and return Supabase client"""
    supabase_url = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
    supabase_key = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))
    
    if not supabase_url or not supabase_key:
        st.error("Supabase credentials not found! Please set SUPABASE_URL and SUPABASE_KEY")
        return None
    
    return create_client(supabase_url, supabase_key)

# Database operations
class SupabaseDB:
    def __init__(self):
        self.client = get_supabase_client()
    
    # ==================== COMPLAINTS ====================
    def create_complaint(self, data: dict):
        """Insert a new complaint"""
        try:
            result = self.client.table('complaints').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error creating complaint: {str(e)}")
            return None
    
    def get_complaint_by_id(self, tracking_id: str):
        """Get complaint by tracking ID"""
        try:
            result = self.client.table('complaints').select("*").eq('tracking_id', tracking_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error fetching complaint: {str(e)}")
            return None
    
    def get_all_complaints(self, filters=None):
        """Get all complaints with optional filters"""
        try:
            query = self.client.table('complaints').select("*")
            
            if filters:
                if filters.get('district'):
                    query = query.eq('district', filters['district'])
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                if filters.get('severity'):
                    query = query.eq('severity', filters['severity'])
                if filters.get('issue_type'):
                    query = query.eq('issue_type', filters['issue_type'])
            
            result = query.order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            st.error(f"Error fetching complaints: {str(e)}")
            return []
    
    def update_complaint_status(self, tracking_id: str, status: str, admin_notes: str = ""):
        """Update complaint status"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            if admin_notes:
                update_data['admin_notes'] = admin_notes
            
            result = self.client.table('complaints').update(update_data).eq('tracking_id', tracking_id).execute()
            
            # Log the update
            self.log_complaint_update(tracking_id, status, admin_notes)
            
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error updating complaint: {str(e)}")
            return None
    
    # ==================== DEPARTMENTS ====================
    def get_all_departments(self):
        """Get all departments"""
        try:
            result = self.client.table('departments').select("*").execute()
            return result.data if result.data else []
        except Exception as e:
            st.error(f"Error fetching departments: {str(e)}")
            return []
    
    def get_department_by_name(self, name: str):
        """Get department by name"""
        try:
            result = self.client.table('departments').select("*").eq('name', name).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            return None
    
    # ==================== COMPLAINT UPDATES ====================
    def log_complaint_update(self, tracking_id: str, new_status: str, notes: str = ""):
        """Log complaint status update"""
        try:
            data = {
                'tracking_id': tracking_id,
                'status': new_status,
                'notes': notes,
                'updated_at': datetime.now().isoformat()
            }
            self.client.table('complaint_updates').insert(data).execute()
        except Exception as e:
            print(f"Error logging update: {str(e)}")
    
    def get_complaint_history(self, tracking_id: str):
        """Get complaint update history"""
        try:
            result = self.client.table('complaint_updates').select("*").eq('tracking_id', tracking_id).order('updated_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            return []
    
    # ==================== NOTIFICATIONS ====================
    def log_notification(self, tracking_id: str, notification_type: str, recipient: str, message: str, status: str = "sent"):
        """Log notification sent"""
        try:
            data = {
                'tracking_id': tracking_id,
                'type': notification_type,
                'recipient': recipient,
                'message': message,
                'status': status,
                'sent_at': datetime.now().isoformat()
            }
            self.client.table('notifications_log').insert(data).execute()
        except Exception as e:
            print(f"Error logging notification: {str(e)}")
    
    # ==================== ANALYTICS ====================
    def get_complaint_stats(self):
        """Get complaint statistics"""
        try:
            all_complaints = self.get_all_complaints()
            
            total = len(all_complaints)
            by_status = {}
            by_district = {}
            by_severity = {}
            by_type = {}
            
            for complaint in all_complaints:
                # By status
                status = complaint.get('status', 'Unknown')
                by_status[status] = by_status.get(status, 0) + 1
                
                # By district
                district = complaint.get('district', 'Unknown')
                by_district[district] = by_district.get(district, 0) + 1
                
                # By severity
                severity = complaint.get('severity', 'Unknown')
                by_severity[severity] = by_severity.get(severity, 0) + 1
                
                # By type
                issue_type = complaint.get('issue_type', 'Unknown')
                by_type[issue_type] = by_type.get(issue_type, 0) + 1
            
            return {
                'total': total,
                'by_status': by_status,
                'by_district': by_district,
                'by_severity': by_severity,
                'by_type': by_type
            }
        except Exception as e:
            st.error(f"Error getting stats: {str(e)}")
            return {}
    
    # ==================== FILE UPLOAD ====================
    def upload_image(self, file, tracking_id: str):
        """Upload image to Supabase Storage"""
        try:
            file_name = f"{tracking_id}_{datetime.now().timestamp()}.png"
            file_path = f"complaints/{file_name}"
            
            # Upload to Supabase storage
            result = self.client.storage.from_('complaint-images').upload(
                file_path, 
                file,
                file_options={"content-type": "image/png"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_('complaint-images').get_public_url(file_path)
            
            return public_url
        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            return None