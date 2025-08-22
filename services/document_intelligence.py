import os
import logging
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
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
        Returns extracted text content
        """
        try:
            logger.info(f"Analyzing document: {file_path}")
            
            with open(file_path, 'rb') as file:
                # Use prebuilt-document model for general document analysis
                poller = self.client.begin_analyze_document(
                    "prebuilt-document", 
                    document=file
                )
                result = poller.result()
            
            # Extract all text content
            full_text = ""
            
            # Extract text from pages
            for page_idx, page in enumerate(result.pages):
                page_text = f"\n--- Page {page_idx + 1} ---\n"
                
                # Extract lines from page
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        page_text += line.content + "\n"
                
                full_text += page_text
            
            # Extract tables as text
            if hasattr(result, 'tables') and result.tables:
                for table_idx, table in enumerate(result.tables):
                    full_text += f"\n--- Table {table_idx + 1} ---\n"
                    
                    # Convert table to text format
                    table_rows = {}
                    for cell in table.cells:
                        row_idx = cell.row_index
                        if row_idx not in table_rows:
                            table_rows[row_idx] = {}
                        table_rows[row_idx][cell.column_index] = cell.content
                    
                    # Format table as text
                    for row_idx in sorted(table_rows.keys()):
                        row = table_rows[row_idx]
                        row_text = " | ".join([row.get(col_idx, "") for col_idx in sorted(row.keys())])
                        full_text += row_text + "\n"
            
            # Extract key-value pairs as text
            if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                full_text += "\n--- Key-Value Pairs ---\n"
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value:
                        full_text += f"{kv_pair.key.content}: {kv_pair.value.content}\n"
            
            logger.info("Document analysis completed successfully")
            return {
                'content': full_text.strip(),
                'page_count': len(result.pages)
            }
            
        except HttpResponseError as e:
            logger.error(f"Azure Document Intelligence API error: {str(e)}")
            raise Exception(f"Document analysis failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            raise Exception(f"Document analysis failed: {str(e)}")
    
    def extract_text_from_image(self, file_path):
        """
        Extract text from image files using OCR
        """
        try:
            logger.info(f"Extracting text from image: {file_path}")
            
            with open(file_path, 'rb') as file:
                poller = self.client.begin_analyze_document(
                    "prebuilt-read",
                    document=file
                )
                result = poller.result()
            
            extracted_text = ""
            for page_idx, page in enumerate(result.pages):
                page_text = f"\n--- Page {page_idx + 1} ---\n"
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        page_text += line.content + "\n"
                extracted_text += page_text
            
            logger.info("OCR extraction completed successfully")
            return {
                'content': extracted_text.strip(),
                'page_count': len(result.pages)
            }
            
        except HttpResponseError as e:
            logger.error(f"Azure Document Intelligence OCR API error: {str(e)}")
            raise Exception(f"OCR extraction failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            raise Exception(f"OCR extraction failed: {str(e)}")
