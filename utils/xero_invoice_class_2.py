from flask import Flask, redirect, request
import json
from utils.config_setup import Config
from utils.xero_token_manager import XeroTokenManager
from utils.xero_api_wrapper import setup_flask_wrapper, create_xero_invoice
import sys
import io
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



class XeroInvoiceApp:
    def __init__(self, invoice_data=None):
        # Load configuration
        self.config = Config()
        
        # Store invoice data
        self.invoice_data = invoice_data
        
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # Initialize token manager
        self.token_manager = XeroTokenManager(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            redirect_uri=self.config.redirect_uri,
            token_url=self.config.token_url,
            auth_url=self.config.auth_url
        )
        
        # Setup Flask wrapper
        setup_flask_wrapper(self.app, self.config)
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Set up all Flask routes"""
        
        @self.app.route("/")
        def login():
            """Redirect user to Xero login"""
            scope = "accounting.invoices offline_access"
            auth_url = self.token_manager.get_auth_url(scope)
            return redirect(auth_url)
        
        @self.app.route("/callback")
        def callback():
            """Callback after Xero login - creates invoice"""
            code = request.args.get("code")
            if not code:
                return {"error": "No authorization code provided"}, 400
            
            # Exchange code for tokens and save them
            token_response, tenant_id = self.token_manager.handle_initial_auth(code)
            
            if not token_response or not tenant_id:
                return {"error": "Failed to authenticate with Xero"}, 500
            
            try:
                # Check if invoice data exists
                if not self.invoice_data:
                    return {"error": "No invoice data provided. Use set_invoice_data() first."}, 400
                    
                resp = create_xero_invoice(self.invoice_data, tenant_id)
                return resp.json()
            except Exception as e:
                return {"error": f"Failed to create invoice: {str(e)}"}, 500
    
    def set_invoice_data(self, invoice_data):
        """Method to update invoice data after initialization"""
        self.invoice_data = invoice_data
        return self.invoice_data
    
    def run(self, port=8000, debug=True):
        """Run the Flask app"""
        self.app.run(port=port, debug=debug)
    
    def get_app(self):
        """Return the Flask app instance (useful for production servers)"""
        return self.app


# For direct script execution (testing)
if __name__ == "__main__":
    # Sample invoice data for testing
    test_invoice_data = {
        "Type": "ACCREC",
        "Contact": {
            "Name": "bieber2",
            "Address": "CG13, Seraya Apartment, Jalan Seksyen 3/1a, Taman Kajang Utama, 43000",
            "Number": 60126665510
        },
        "Date": "2025-08-13",
        "ExpiryDate": "2025-08-23",
        "LineItems": [
            {
                "Description": "Door Knob Replacement ( Room 3)",
                "Quantity": 1,
                "UnitAmount": 150.00,
                "AccountCode": "200"
            },
            {
                "Description": "Power Socket ( Hall + Room 3)",
                "Quantity": 2,
                "UnitAmount": 75.00,
                "AccountCode": "200"
            },
            {
                "Description": "Trip Inspection with diagnosis",
                "Quantity": 1,
                "UnitAmount": 150.00,
                "AccountCode": "200"
            }
        ],
        "Title": "Invoice",
        "Summary": "Installation of door knobs, power sockets and trip inspection with diagnosis at Saiful Amir Bin Mat Rasid's residence."
    }
    
    # Create and run the app
    xero_app = XeroInvoiceApp(invoice_data=test_invoice_data)
    print("🚀 Starting Xero Invoice App on http://127.0.0.1:8000")
    print("📋 Invoice data loaded:", json.dumps(test_invoice_data, indent=2))
    xero_app.run(port=8000, debug=True)