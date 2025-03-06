# Hackts-BypassATS

Hackts-BypassATS is a tool designed to optimize your PDF resume by discreetly embedding relevant job keywords into the file. This increases your chances of passing Applicant Tracking Systems (ATS) filters by ensuring your resume is rich in the necessary keywords.

## Features

- **Keyword Extraction:** Extracts the most relevant keywords from a job description using YAKE!
- **LinkedIn Scraping:** Automatically scrapes job postings from LinkedIn to obtain the job description and title.
- **Manual Mode:** Allows you to input the job description and title manually.
- **PDF Optimization:** Embeds keywords into your existing PDF resume without altering the visible content.
- **Automated Output:** Saves an optimized version of your resume with a new, descriptive filename.

## Prerequisites

- Python 3.6 or higher
- Pip package manager

### Required Libraries

- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- [YAKE!](https://github.com/LIAAD/yake)
- [Requests](https://docs.python-requests.org/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Colorama](https://pypi.org/project/colorama/)

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/IIIDei/Hackts-BypassATS.git
   cd Hackts-BypassATS
   ```

2. **(Optional) Create a Virtual Environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install the Dependencies:**
   If a `requirements.txt` file exists, run:
   ```bash
   pip install -r requirements.txt
   ```
   Otherwise, install the required libraries individually:
   ```bash
   pip install pymupdf yake requests beautifulsoup4 colorama
   ```

## Configuration

- **Set Your Resume File:**  
  Open the main Python script and modify the `NOM_CV` variable to the name of your resume PDF file. Ensure that your resume is located in the same directory as the script.
  ```python
  NOM_CV = "Your_Resume.pdf"  # Replace with your resume file name
  ```

- **Language Setting for Keyword Extraction:**  
  By default, the script is configured to extract keywords in French (using `language = "fr"`).  
  If your job posting is in another language, change this value accordingly in the `extraire_mots_cles` function.

## Usage

### Automatic Mode (LinkedIn Scraping)

1. **Run the Script:**
   ```bash
   python main.py
   ```

2. **Enter the LinkedIn URL:**  
   When prompted, input the URL of a LinkedIn job posting. The script will:
   - Scrape the job posting for the job description and title.
   - Extract relevant keywords from the job description.
   - Embed the keywords and the job title into your PDF resume.
   - Save a new version of your resume in the same directory.

### Manual Mode

1. **Run the Script in Manual Mode:**
   ```bash
   python main.py -m
   ```

2. **Choose Your Input Method:**  
   - **Option 1:** Directly type or paste the job description into the terminal (finish input by pressing Ctrl+D).
   - **Option 2:** Use a temporary text editor (nano by default) to enter the job description.

3. **Enter the Job Title:**  
   After providing the description, you will be prompted to input the job title.

4. **Processing and Output:**  
   The script will process your inputs, extract keywords, embed them into your PDF resume, and save the optimized version.

## Output

- **Optimized Resume File:**  
  The new PDF resume will be saved in the same directory as the original file. The output filename will include the original filename and a sanitized version of the job title, for example:
  ```
  [Your_Resume] [Job_Title].pdf
  ```

## Contributing

Feel free to fork the repository and submit pull requests for enhancements or bug fixes. Contributions are welcome!

## Disclaimer

This tool is intended for personal use to optimize your resume. Use it responsibly and be mindful of ethical considerations when modifying your CV for ATS systems.
