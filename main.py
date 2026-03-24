
from utils.ds_bot import LLM
from utils.flair_class import Flair_tools
import json
import ast
from utils.xero_invoice_class_2 import XeroInvoiceApp
import sys
import io

pdf = rf"C:\Users\tvlan\OneDrive\Documents\Python Files\37.4 Xero_PII\Quotation_Sample.pdf"


# Force stdout to use UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def Xero_Invoice_App(pdf):
    ds = LLM(pdf)
    pdf_text = ds.extract_pdf(pdf)

    flair = Flair_tools(pdf_text)
    redacted_text , entity_map = flair.flair_redactor()
    print(redacted_text)

    print(pdf_text)

    json_output = ds.deepseek(redacted_text)
    print(json_output)

    output = json.loads(json_output)
    print(output)

    undo_redaction = flair.flair_restorer(str(output), entity_map)
    restored_dict = ast.literal_eval(undo_redaction)

    print(type(restored_dict), type(output))
    #print(jsonify)

    app = XeroInvoiceApp(restored_dict)
    app.run(port=8000, debug=True)

if __name__ == "__main__":
    Xero_Invoice_App(pdf)