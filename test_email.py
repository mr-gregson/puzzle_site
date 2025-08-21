"""
Email testing script for production deployment.
Run this script to test email functionality before going live.
"""
import os
from flask import Flask
from flask_mail import Mail, Message
from app import create_app

def test_email():
    """Test email functionality."""
    app = create_app()
    
    with app.app_context():
        mail = Mail(app)
        
        # Check if email is configured
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("❌ Email not configured. Please set MAIL_USERNAME and MAIL_PASSWORD in your .env file")
            return False
        
        try:
            # Create test message
            msg = Message(
                subject="Puzzle Site - Email Test",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[app.config['PUZZLE_SITE_ADMIN']]
            )
            msg.body = """
This is a test email from your Puzzle Site application.

If you're receiving this email, your email configuration is working correctly!

Test details:
- MAIL_SERVER: {mail_server}
- MAIL_PORT: {mail_port}
- MAIL_USE_TLS: {mail_tls}
- From: {sender}
- To: {recipient}

Timestamp: {timestamp}
            """.format(
                mail_server=app.config['MAIL_SERVER'],
                mail_port=app.config['MAIL_PORT'],
                mail_tls=app.config['MAIL_USE_TLS'],
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipient=app.config['PUZZLE_SITE_ADMIN'],
                timestamp=str(os.environ.get('DATE', 'Unknown'))
            )
            
            print(f"📧 Sending test email to {app.config['PUZZLE_SITE_ADMIN']}...")
            mail.send(msg)
            print("✅ Test email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send test email: {e}")
            print("\n🔍 Troubleshooting tips:")
            print("1. Check your MAIL_USERNAME and MAIL_PASSWORD are correct")
            print("2. For Gmail, use an 'App Password' instead of your regular password")
            print("3. Verify MAIL_SERVER and MAIL_PORT settings")
            print("4. Check firewall/network settings")
            return False

if __name__ == '__main__':
    print("🧪 Testing email configuration...")
    success = test_email()
    
    if success:
        print("\n🎉 Email test completed successfully!")
    else:
        print("\n💥 Email test failed. Please check your configuration.")
        exit(1)