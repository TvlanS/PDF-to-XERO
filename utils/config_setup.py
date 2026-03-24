import yaml
import pyprojroot

root = pyprojroot.here()

class Config():
    def __init__ (self):
        import os
        config_dir = os.path.join(root, "config")
        config_path = os.path.join(config_dir, "app_config.yml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

            # Helper function to clean YAML string values (strip quotes and whitespace)
            def clean_value(value):                
                if isinstance(value, str):
                    # Strip leading/trailing whitespace and quotes
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                return value

            self.api_key = clean_value(config["deepseek"]["api_key"])
            self.website_url = clean_value(config["deepseek"]["website_url"])
            self.prompt = clean_value(config["prompt"]["system_prompt"])
            self.xero_prompt = clean_value(config["prompt"]["prompt_xero"])

            # Xero credentials
            xero_config = config["Xero"]
            self.client_id = clean_value(xero_config["CLIENT_ID"])
            self.client_secret = clean_value(xero_config["CLIENT_SECRET"])
            self.redirect_uri = clean_value(xero_config["REDIRECT_URI"])
            self.auth_url = clean_value(xero_config["AUTH_URL"])
            self.token_url = clean_value(xero_config["TOKEN_URL"])

            # Token management settings
            self.token_storage_path = clean_value(xero_config.get("token_storage_path", "config/tokens"))
            self.token_refresh_threshold = int(clean_value(xero_config.get("token_refresh_threshold", 300)))
        
            




