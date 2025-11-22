"""
Admin export service for reports.
"""

import logging
from typing import Optional
from pathlib import Path
from admin.services.admin_user_service import admin_user_service
from admin.services.admin_license_service import admin_license_service
from admin.services.admin_analytics_service import admin_analytics_service

logger = logging.getLogger(__name__)


class AdminExportService:
    """Handles export operations."""
    
    def export_users_to_excel(self, file_path: str) -> bool:
        """Export all users to Excel."""
        try:
            import pandas as pd
            
            users = admin_user_service.get_all_users()
            
            # Prepare data
            data = []
            for user in users:
                data.append({
                    "UID": user.get("uid", ""),
                    "Email": user.get("email", ""),
                    "Display Name": user.get("display_name", ""),
                    "Email Verified": user.get("email_verified", False),
                    "Disabled": user.get("disabled", False),
                    "License Tier": user.get("license_tier", "none"),
                    "License Expires": user.get("license_expires", ""),
                    "Created At": user.get("created_at", ""),
                    "Last Sign In": user.get("last_sign_in", ""),
                })
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logger.info(f"Exported {len(users)} users to {file_path}")
            return True
            
        except ImportError:
            logger.error("pandas and openpyxl are required for Excel export")
            return False
        except Exception as e:
            logger.error(f"Error exporting users to Excel: {e}", exc_info=True)
            return False
    
    def export_licenses_to_excel(self, file_path: str) -> bool:
        """Export all licenses to Excel."""
        try:
            import pandas as pd
            
            licenses = admin_license_service.get_all_licenses()
            
            # Prepare data
            data = []
            for license_data in licenses:
                data.append({
                    "UID": license_data.get("uid", ""),
                    "Tier": license_data.get("tier", ""),
                    "Expiration Date": license_data.get("expiration_date", ""),
                    "Max Devices": license_data.get("max_devices", 0),
                    "Max Groups": license_data.get("max_groups", 0),
                    "Max Accounts": license_data.get("max_accounts", 0),
                    "Active Devices": len(license_data.get("active_devices", [])),
                    "Created At": license_data.get("created_at", ""),
                })
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logger.info(f"Exported {len(licenses)} licenses to {file_path}")
            return True
            
        except ImportError:
            logger.error("pandas and openpyxl are required for Excel export")
            return False
        except Exception as e:
            logger.error(f"Error exporting licenses to Excel: {e}", exc_info=True)
            return False
    
    def export_analytics_to_pdf(self, file_path: str) -> bool:
        """Export analytics report to PDF."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from datetime import datetime
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph("Admin Analytics Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Date
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_para = Paragraph(f"Generated: {date_str}", styles['Normal'])
            story.append(date_para)
            story.append(Spacer(1, 0.3*inch))
            
            # Get stats
            user_stats = admin_analytics_service.get_user_stats()
            license_stats = admin_analytics_service.get_license_stats()
            device_stats = admin_analytics_service.get_device_stats()
            
            # User Stats
            story.append(Paragraph("User Statistics", styles['Heading2']))
            user_data = [
                ["Metric", "Value"],
                ["Total Users", str(user_stats.get("total", 0))],
                ["Active Users", str(user_stats.get("active", 0))],
                ["Disabled Users", str(user_stats.get("disabled", 0))],
                ["New Users (30 days)", str(user_stats.get("new_last_30_days", 0))],
            ]
            user_table = Table(user_data)
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(user_table)
            story.append(Spacer(1, 0.3*inch))
            
            # License Stats
            story.append(Paragraph("License Statistics", styles['Heading2']))
            license_data = [
                ["Metric", "Value"],
                ["Total Licenses", str(license_stats.get("total", 0))],
                ["Active Licenses", str(license_stats.get("active", 0))],
                ["Expired Licenses", str(license_stats.get("expired", 0))],
            ]
            for tier in ["bronze", "silver", "gold", "premium"]:
                license_data.append([
                    f"{tier.capitalize()} Tier",
                    str(license_stats.get("by_tier", {}).get(tier, 0))
                ])
            
            license_table = Table(license_data)
            license_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(license_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Device Stats
            story.append(Paragraph("Device Statistics", styles['Heading2']))
            device_data = [
                ["Metric", "Value"],
                ["Total Devices", str(device_stats.get("total", 0))],
                ["Average per User", str(device_stats.get("average_per_user", 0))],
                ["Users with Devices", str(device_stats.get("users_with_devices", 0))],
                ["Users without Devices", str(device_stats.get("users_without_devices", 0))],
            ]
            device_table = Table(device_data)
            device_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(device_table)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Exported analytics report to {file_path}")
            return True
            
        except ImportError:
            logger.error("reportlab is required for PDF export")
            return False
        except Exception as e:
            logger.error(f"Error exporting analytics to PDF: {e}", exc_info=True)
            return False


# Global admin export service instance
admin_export_service = AdminExportService()

