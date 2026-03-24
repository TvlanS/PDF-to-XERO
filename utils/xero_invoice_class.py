from flask import Flask, redirect, request
import json
from utils.config_setup import Config
from utils.xero_token_manager import XeroTokenManager
from utils.xero_api_wrapper import setup_flask_wrapper, create_xero_invoice

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
                # Create invoice using stored invoice data
                if not self.invoice_data:
                    return {"error": "No invoice data provided"}, 400
                    
                resp = create_xero_invoice(self.invoice_data, tenant_id)
                return resp.json()
            except Exception as e:
                return {"error": f"Failed to create invoice: {str(e)}"}, 500
    
    def set_invoice_data(self, invoice_data):
        """Method to update invoice data after initialization"""
        self.invoice_data = invoice_data
    
    def run(self, port=8000, debug=True):
        """Run the Flask app"""
        # Setup Flask wrapper with the app
        setup_flask_wrapper(self.app, self.config)
        
        # Run the app
        self.app.run(port=port, debug=debug)
    
    def get_app(self):
        """Return the Flask app instance (useful for production servers)"""
        setup_flask_wrapper(self.app, self.config)
        return self.app

