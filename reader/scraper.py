import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


class WebScraper:
    def __init__(self, url, max_depth=2, markdown_dir="markdown", files_dir="files"):
        self.url = url
        self.max_depth = max_depth
        self.soup = None
        self.title = ""
        self.content = ""
        self.pdf_files = []
        self.other_files = []  # Non-PDF documents
        self.visited_urls = set()
        self.markdown_dir = markdown_dir
        self.files_dir = files_dir  # Single directory for all files
        
    def scrape(self):
        try:
            # Send a GET request to the URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            
            self.soup = BeautifulSoup(response.text, 'html.parser')
            
            if self.soup.title:
                self.title = self.soup.title.string.strip()
            else:
                self.title = "No Title"
            
            # Extract main content
            self._extract_content()
            
            # Find files from current page and linked pages
            self._find_files_recursive(self.url, 0)
            
            return True
        except Exception as e:
            print(f"Error scraping {self.url}: {e}")
            return False
    
    def _extract_content(self):
        content_parts = []
        
        # Find all relevant elements
        elements = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table', 'img'])
        
        # Track whether we've seen a heading yet
        first_heading_found = False
        
        # Process elements, only including content after the first heading
        for element in elements:
            # Check if this is a heading
            if element.name.startswith('h') and not first_heading_found:
                first_heading_found = True
                level = int(element.name[1])
                content_parts.append(f"{'#' * level} {element.get_text().strip()}\n\n")
            # Only process other elements if we've already found the first heading
            elif first_heading_found:
                if element.name.startswith('h'):
                    level = int(element.name[1])
                    content_parts.append(f"{'#' * level} {element.get_text().strip()}\n\n")
                elif element.name == 'p':
                    text = element.get_text().strip()
                    if text:
                        content_parts.append(f"{text}\n\n")
                elif element.name == 'ul' or element.name == 'ol':
                    for li in element.find_all('li'):
                        text = li.get_text().strip()
                        if text:
                            content_parts.append(f"- {text}\n")
                    content_parts.append("\n")
                elif element.name == 'table':
                    # Simple table handling
                    content_parts.append("| ")
                    
                    # Headers
                    headers = element.find_all('th')
                    if headers:
                        content_parts.append(" | ".join(header.get_text().strip() for header in headers))
                        content_parts.append(" |\n| ")
                        content_parts.append(" | ".join("---" for _ in headers))
                        content_parts.append(" |\n")
                    
                    # Rows
                    for row in element.find_all('tr'):
                        cells = row.find_all(['td'])
                        if cells:
                            content_parts.append("| ")
                            content_parts.append(" | ".join(cell.get_text().strip() for cell in cells))
                            content_parts.append(" |\n")
                    content_parts.append("\n")
                elif element.name == 'img':
                    src = element.get('src', '')
                    alt = element.get('alt', 'Image')
                    if src:
                        # Handle relative URLs
                        if not (src.startswith('http://') or src.startswith('https://')):
                            base_url = urlparse(self.url)
                            if src.startswith('/'):
                                src = f"{base_url.scheme}://{base_url.netloc}{src}"
                            else:
                                src = f"{base_url.scheme}://{base_url.netloc}/{src}"
                        content_parts.append(f"![{alt}]({src})\n\n")
        
        # If no heading was found, add a default heading with the page title
        if not first_heading_found:
            content_parts.insert(0, f"# {self.title}\n\n")
        
        self.content = "".join(content_parts)
    
    def _get_soup_from_url(self, url):

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error getting soup from {url}: {e}")
            return None
    
    def _find_files_recursive(self, url, depth=0):
        # Skip if we've visited this URL before
        if url in self.visited_urls:
            return
        
        # Mark this URL as visited
        self.visited_urls.add(url)
        
        # Don't process if we're already at max depth
        if depth > self.max_depth:
            return
        
        # Get BeautifulSoup object from URL
        if depth == 0 and self.soup:
            # Use existing soup for root URL
            soup = self.soup
        else:
            soup = self._get_soup_from_url(url)
            if not soup:
                return
        
        # Parse domain from URL
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # List of document extensions to look for
        pdf_extension = '.pdf'
        other_document_extensions = [
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
            '.txt', '.rtf', '.csv', '.odt', '.ods', '.odp'
        ]
        
        # Find document files in current page
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            
            # Skip empty links
            if not href:
                continue
                
            # Convert relative URLs to absolute
            full_url = urljoin(url, href)
            
            # Skip link if it points to a different domain (optional)
            # if not full_url.startswith(domain):
            #     continue
            
            # Get the lowercase URL for extension checking
            lower_url = full_url.lower()
            
            # Check if the URL points to a PDF file
            if lower_url.endswith(pdf_extension):
                # Add PDF to list if not already there
                file_info = {
                    'url': full_url,
                    'text': link.get_text().strip() or os.path.basename(full_url),
                    'type': 'pdf'
                }
                
                # Check if this PDF URL is already in our list
                if not any(pdf['url'] == full_url for pdf in self.pdf_files):
                    self.pdf_files.append(file_info)
            
            # Check if the URL points to other document types
            elif any(lower_url.endswith(ext) for ext in other_document_extensions):
                # Add document to other_files list if not already there
                file_info = {
                    'url': full_url,
                    'text': link.get_text().strip() or os.path.basename(full_url),
                    'type': 'document',
                    'extension': os.path.splitext(lower_url)[1]
                }
                
                # Check if this document URL is already in our list
                if not any(doc['url'] == full_url for doc in self.other_files):
                    self.other_files.append(file_info)
        
        # If we're not at max depth, follow links
        if depth < self.max_depth:
            # Find all links on the page
            links_to_follow = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                
                # Skip empty links or document files we've already processed
                if not href or any(href.lower().endswith(ext) for ext in [pdf_extension] + other_document_extensions):
                    continue
                
                # Convert relative URLs to absolute
                full_url = urljoin(url, href)
                
                # Skip if it's not HTTP/HTTPS
                if not (full_url.startswith('http://') or full_url.startswith('https://')):
                    continue
                
                # Skip if already visited
                if full_url in self.visited_urls:
                    continue
                
                links_to_follow.append(full_url)
            
            # Follow links
            for link_url in links_to_follow:
                self._find_files_recursive(link_url, depth + 1)
    
    def download_files(self):
        """Download all files (PDF and other document types) to the files directory"""
        all_files = []
        
        # Download PDF files to the files directory
        pdf_files = self.download_pdfs(output_dir=self.files_dir)
        all_files.extend(pdf_files)
        
        # Download other document files to the same files directory
        other_files = self.download_other_files(output_dir=self.files_dir)
        all_files.extend(other_files)
        
        return all_files
    
    def download_pdfs(self, output_dir=None):
        # Use the provided output_dir or fallback to the files_dir
        if output_dir is None:
            output_dir = self.files_dir
            
        if not self.pdf_files:
            print("No PDF files found on the page")
            return []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        downloaded_files = []
        
        # Download each PDF file
        for i, pdf in enumerate(self.pdf_files):
            try:
                pdf_url = pdf['url']
                
                # Create a filename from the link text or URL
                if pdf['text'] and pdf['text'] != os.path.basename(pdf_url):
                    # Use the link text if available and not just the filename
                    filename = re.sub(r'[^\w\s-]', '', pdf['text'].lower())
                    filename = re.sub(r'[\s-]+', '_', filename)
                    filename = f"{filename}.pdf"
                else:
                    # Use the filename from the URL
                    filename = os.path.basename(pdf_url)
                
                # Make sure filename is unique
                if filename in [os.path.basename(f) for f in downloaded_files]:
                    filename = f"{os.path.splitext(filename)[0]}_{i}{os.path.splitext(filename)[1]}"
                
                output_path = os.path.join(output_dir, filename)
                
                if os.path.exists(output_path):
                    # Check file size to verify it's not a corrupted download
                    if os.path.getsize(output_path) > 0:
                        print(f"File already exists, skipping: {output_path}")
                        downloaded_files.append(output_path)
                        continue
                    else:
                        print(f"File exists but appears empty/corrupted, redownloading: {output_path}")

                response = requests.get(pdf_url, stream=True)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(output_path)
                print(f"Downloaded {output_path}")
                
            except Exception as e:
                print(f"Error downloading {pdf.get('url')}: {e}")
        
        return downloaded_files
    
    def download_other_files(self, output_dir=None):
        # Use the provided output_dir or fallback to the files_dir
        if output_dir is None:
            output_dir = self.files_dir
            
        if not self.other_files:
            print("No other document files found on the page")
            return []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        downloaded_files = []
        
        # Download each document file
        for i, doc in enumerate(self.other_files):
            try:
                doc_url = doc['url']
                
                # Create a filename from the link text or URL
                if doc['text'] and doc['text'] != os.path.basename(doc_url):
                    # Use the link text if available and not just the filename
                    filename = re.sub(r'[^\w\s-]', '', doc['text'].lower())
                    filename = re.sub(r'[\s-]+', '_', filename)
                    filename = f"{filename}{doc['extension']}"
                else:
                    # Use the filename from the URL
                    filename = os.path.basename(doc_url)
                
                # Make sure filename is unique
                if filename in [os.path.basename(f) for f in downloaded_files]:
                    filename = f"{os.path.splitext(filename)[0]}_{i}{os.path.splitext(filename)[1]}"
                
                output_path = os.path.join(output_dir, filename)
                
                if os.path.exists(output_path):
                    # Check file size to verify it's not a corrupted download
                    if os.path.getsize(output_path) > 0:
                        print(f"File already exists, skipping: {output_path}")
                        downloaded_files.append(output_path)
                        continue
                    else:
                        print(f"File exists but appears empty/corrupted, redownloading: {output_path}")

                response = requests.get(doc_url, stream=True)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(output_path)
                print(f"Downloaded {output_path}")
                
            except Exception as e:
                print(f"Error downloading {doc.get('url')}: {e}")
        
        return downloaded_files
    
    def save_as_markdown(self, output_path=None, output_dir=None):
        if not self.content:
            raise ValueError("No content to save. Run scrape() first.")
        
        # Use either the specified output directory or default markdown directory
        if output_dir is None:
            output_dir = self.markdown_dir
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        if not output_path:
            # Create a filename from the title
            filename = re.sub(r'[^\w\s-]', '', self.title.lower())
            filename = re.sub(r'[\s-]+', '_', filename)
            output_path = os.path.join(output_dir, f"{filename}.md")
        elif not os.path.isabs(output_path) and output_dir:
            # If output_path is relative and output_dir is specified, join them
            output_path = os.path.join(output_dir, output_path)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        # Write the content to the file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
        
        return output_path
    
    def get_markdown(self):
        if not self.content:
            raise ValueError("No content available. Run scrape() first.")
        
        return self.content
    
    def get_pdf_files(self):
        return self.pdf_files
    
    def get_other_files(self):
        return self.other_files
    
    def run(self):
        """
        Main method that executes the complete web scraping process
        """
        # Scrape the URL
        if not self.scrape():
            print("Failed to scrape the URL")
            return
            
        # Report found files
        pdf_count = len(self.get_pdf_files())
        other_count = len(self.get_other_files())
        
        print(f"\nFound {pdf_count} PDF files")
        print(f"Found {other_count} other document files")
        
        # Download all files to the same directory
        downloaded_files = self.download_files()
        
        if downloaded_files:
            print(f"\nDownloaded {len(downloaded_files)} files to {self.files_dir}")
        
        # Save content as markdown
        markdown_path = self.save_as_markdown()
        print(f"\nContent saved to {markdown_path}")


# Example usage
if __name__ == "__main__":
    # Example URL
    url = "https://student.uit.edu.vn/content/huong-dan-sinh-vien-dai-hoc-he-chinh-quy-thuc-hien-cac-quy-dinh-ve-chuan-qua-trinh-va-chuan"
    
    # Create a WebScraper instance with max_depth and custom output directories
    # Now using a single directory for all files
    scraper = WebScraper(url, max_depth=2, markdown_dir="output/markdown", files_dir="output/files")
    
    # Run the complete scraping process
    scraper.run()
