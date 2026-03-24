# PDF to XERO Invoice

Convert 3rd party PDF invoices to XERO with PII protection.

## Motivation

Processing third-party invoices manually is time-consuming and error-prone. This project streamlines the invoicing workflow by automating the extraction of invoice data from PDFs, protecting Personally Identifiable Information (PII) during processing, and seamlessly creating invoices in Xero accounting software.

<p align="center">
  <img src="https://github.com/TvlanS/PDF-to-XERO/blob/f7800ecfe23df1959b71d1a1d3dfe3c135961083/Sample/Sample_PDF_image.png?raw=true" width="600" alt="Sample PDF">
  <br>
  <em>Sample PDF Document</em>
</p>

<p align="center">
  <img src="https://github.com/TvlanS/PDF-to-XERO/blob/f7800ecfe23df1959b71d1a1d3dfe3c135961083/Sample/Sample_Xero_image.png?raw=true" width="600" alt="Sample Xero Output">
  <br>
  <em>Sample Xero Output</em>
</p>

## Key Features

- **PDF Text Extraction**: Uses `pypdf` to extract text from PDF invoices.
- **PII Redaction**: Leverages Flair's Named Entity Recognition (NER) model to identify and redact sensitive information (names, addresses, phone numbers, etc.) before sending data to external APIs.
- **LLM-Powered Invoice Formatting**: Sends redacted text to DeepSeek LLM via OpenAI-compatible API to structure invoice data into Xero-compatible JSON format.
- **PII Restoration**: Replaces redacted placeholders with original PII after LLM processing, maintaining data integrity.
- **Xero API Integration**: Creates invoices in Xero using OAuth2 authentication with automatic token refresh.
- **Web Interface**: Provides a simple Flask web app to handle OAuth authorization flow.
- **Token Management**: Securely stores and refreshes Xero API tokens.

## Tech Stack

- **Python 3.8+**
- **Flask** – Web framework for OAuth flow
- **Flair NLP** – Named Entity Recognition for PII detection
- **PyTorch** – Deep learning backend for Flair
- **pypdf** – PDF text extraction
- **DeepSeek API** – LLM for invoice data structuring (via OpenAI-compatible API)
- **Xero API** – Accounting platform integration
- **Requests** – HTTP client for API calls
- **PyYAML** – Configuration file parsing
- **pyprojroot** – Project root detection

## Installation

### Prerequisites

- Python 3.8 or higher
- A DeepSeek API key (sign up at [deepseek.com](https://platform.deepseek.com/))
- Xero developer account with a registered app (get `CLIENT_ID`, `CLIENT_SECRET`, and `REDIRECT_URI`)

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Xero_PII
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is not present, install the packages manually:
   ```bash
   pip install flask flair torch pypdf openai requests pyyaml pyprojroot
   ```
   **Note**: Flair requires PyTorch (`torch`). The command above installs the CPU version. If you need GPU support, install the appropriate `torch` version from [pytorch.org](https://pytorch.org/get-started/locally/) before installing `flair`.

4. **Configure the application**
   - Copy `config/app_config.yml.example` to `config/app_config.yml` (if an example exists) or edit the existing `app_config.yml`.
   - Fill in your DeepSeek API key and Xero credentials.

## Configuration

Edit `config/app_config.yml` with your credentials:

```yaml
deepseek:
  api_key: "your-deepseek-api-key"
  website_url: "https://api.deepseek.com"

prompt:
  prompt_xero: |
    You are an assistant that prepares quotation data for the Xero Accounting API based of pdf extract given to you.
    # ... (prompt remains as provided)

Xero:
  CLIENT_ID: "your-xero-client-id"
  CLIENT_SECRET: "your-xero-client-secret"
  REDIRECT_URI: "http://localhost:8000/callback"
  AUTH_URL: "https://login.xero.com/identity/connect/authorize"
  TOKEN_URL: "https://identity.xero.com/connect/token"
  token_storage_path: "config/tokens"
  token_refresh_threshold: 300
```

**Note**: The `prompt_xero` section contains the system prompt that instructs the LLM to output JSON in a specific schema. Modify it only if you need to adjust the invoice format.

### Invoice Data Format

The LLM outputs a JSON object that matches Xero's invoice schema. Below is an example of the expected structure (based on the sample PDF):

```json
{
  "Type": "ACCREC",
  "Contact": {
    "Name": "Customer Name",
    "Addresses": [
      {
        "AddressType": "STREET",
        "AddressLine1": "123 Main St",
        "City": "City",
        "Region": "State",
        "PostalCode": "12345",
        "Country": "Country"
      }
    ],
    "Phones": [
      {
        "PhoneType": "MOBILE",
        "PhoneNumber": "+1234567890"
      }
    ]
  },
  "Date": "2025-08-13",
  "ExpiryDate": "2025-08-23",
  "LineItems": [
    {
      "Description": "Service or item description",
      "Quantity": 1,
      "UnitAmount": 150.00,
      "AccountCode": "200"
    }
  ],
  "Title": "Invoice",
  "Summary": "Brief summary of the works."
}
```

## Usage

### 1. Prepare a PDF invoice

Place your PDF invoice in the project directory (or note its path). The sample `Quotation_Sample.pdf` is included for testing.

By default, the application processes `Quotation_Sample.pdf`. To use your own PDF, edit `main.py` and change the `pdf` variable on line 10 to point to your PDF file.

### 2. Run the application

Execute the main script:

```bash
python main.py
```

This will:
- Extract text from the PDF
- Redact PII using Flair NER
- Send redacted text to DeepSeek LLM
- Restore PII and format invoice data
- Start a Flask web server at `http://127.0.0.1:8000`

### 3. Authorize with Xero

Open your browser and navigate to `http://127.0.0.1:8000`. You will be redirected to Xero's login page. After logging in and granting permissions, the app will automatically create an invoice in your Xero organization using the extracted data.

### 4. Verify the invoice

Check your Xero account to confirm the invoice has been created.

### Example Output

A sample Xero invoice created by the application:

![Sample Xero Invoice](Sample_Xero_image.png)

The image shows an invoice generated in Xero from the sample PDF.

## Project Structure

```
Xero_PII/
├── main.py                      # Entry point
├── config/
│   └── app_config.yml           # Configuration file
├── utils/                       # Core modules
│   ├── config_setup.py          # Configuration loader
│   ├── ds_bot.py                # LLM client & PDF extraction
│   ├── flair_class.py           # PII redaction & restoration
│   ├── xero_invoice_class_2.py  # Flask app & invoice creation
│   ├── xero_token_manager.py    # OAuth token management
│   ├── xero_api_wrapper.py      # Xero API wrapper
│   └── token_storage.py         # Token storage utilities
├── Quotation_Sample.pdf         # Sample invoice PDF
└── Sample_Xero_image.png        # Example output screenshot
```

## How It Works

1. **PDF Extraction**: `pypdf` reads the PDF and extracts raw text.
2. **PII Redaction**: Flair NER identifies entities (Person, Location, Organization, etc.) and replaces them with placeholders (e.g., `[PER_1]`, `[LOC_1]`). A mapping dictionary preserves the original values.
3. **LLM Processing**: The redacted text is sent to DeepSeek LLM with a system prompt that instructs it to output a JSON object matching Xero's invoice schema.
4. **PII Restoration**: The placeholders in the LLM output are replaced with the original PII using the mapping dictionary.
5. **Xero Invoice Creation**: A Flask app starts, guiding the user through Xero OAuth authorization. Once authorized, the app sends the formatted invoice data to Xero's API.

## License

Distributed under the MIT License. See `LICENSE` (if present) for more information.

## Acknowledgments

- [Flair NLP](https://github.com/flairNLP/flair) for excellent NER models.
- [DeepSeek](https://www.deepseek.com/) for providing powerful and affordable LLM APIs.
- [Xero](https://developer.xero.com/) for comprehensive accounting APIs.
- [pypdf](https://pypi.org/project/pypdf/) for simple PDF text extraction.

## Support

For issues, questions, or feature requests, please open an issue in the repository.
