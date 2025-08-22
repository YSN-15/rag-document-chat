import os
import logging
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from config import Config

logger = logging.getLogger(__name__)

class DocumentIntelligenceService:
    def __init__(self):
        self.endpoint = Config.AZURE_DI_ENDPOINT
        self.key = Config.AZURE_DI_KEY
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure Document Intelligence credentials not configured")
        
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    def analyze_document(self, file_path):
        """
        Analyze document using Azure Document Intelligence
        Returns extracted text, tables, and metadata
        """
        try:
            with open(file_path, 'rb') as file:
                poller = self.client.begin_analyze_document(
                    "prebuilt-document", 
                    document=file
                )
                result = poller.result()
            
            # Extract text content with page information
            extracted_data = {
                'content': '',
                'pages': [],
                'tables': [],
                'key_value_pairs': [],
                'metadata': {}
            }
            
            # Process pages
            for page_idx, page in enumerate(result.pages):
                page_content = ""
                page_info = {
                    'page_number': page_idx + 1,
                    'content': '',
                    'lines': []
                }
                
                # Extract lines from page
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        line_text = line.content
                        page_content += line_text + "\n"
                        page_info['lines'].append(line_text)
                
                page_info['content'] = page_content
                extracted_data['pages'].append(page_info)
                extracted_data['content'] += f"\n--- Page {page_idx + 1} ---\n" + page_content
            
            # Extract tables
            if hasattr(result, 'tables') and result.tables:
                for table_idx, table in enumerate(result.tables):
                    table_data = {
                        'table_index': table_idx,
                        'row_count': table.row_count,
                        'column_count': table.column_count,
                        'cells': []
                    }
                    
                    for cell in table.cells:
                        table_data['cells'].append({
                            'content': cell.content,
                            'row_index': cell.row_index,
                            'column_index': cell.column_index
                        })
                    
                    extracted_data['tables'].append(table_data)
            
            # Extract key-value pairs
            if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value:
                        extracted_data['key_value_pairs'].append({
                            'key': kv_pair.key.content,
                            'value': kv_pair.value.content
                        })
            
            logger.info(f"Successfully analyzed document: {file_path}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            raise Exception(f"Document analysis failed: {str(e)}")
    
    def extract_text_from_image(self, file_path):
        """
        Extract text from image files using OCR
        """
        try:
            with open(file_path, 'rb') as file:
                poller = self.client.begin_analyze_document(
                    "prebuilt-read",
                    document=file
                )
                result = poller.result()
            
            extracted_text = ""
            for page in result.pages:
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        extracted_text += line.content + "\n"
            
            return {
                'content': extracted_text,
                'pages': [{'page_number': 1, 'content': extracted_text}],
                'tables': [],
                'key_value_pairs': [],
                'metadata': {'extracted_via': 'OCR'}
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            raise Exception(f"OCR extraction failed: {str(e)}")
