import fitz
import yake
import os
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style
import re
import time
import argparse
import tempfile
import subprocess
import sys

init(autoreset=True)

RESUME_FILE = ""     # Fill in your CV file name

def extract_keywords(text, N=400):
    language = "en"     # Set the language of the job posting; default is English ("en")
    max_ngram_size = 2
    deduplication_threshold = 0.7
    deduplication_algo = "seqm"
    custom_kw_extractor = yake.KeywordExtractor(
        lan=language,
        n=max_ngram_size,
        dedupLim=deduplication_threshold,
        dedupFunc=deduplication_algo,
        windowsSize=1,
        top=N,
        features=None
    )
    keywords = custom_kw_extractor.extract_keywords(text)
    keywords_list = [kw for kw, score in keywords]
    return keywords_list

def sanitize_filename(filename):
    return re.sub(r'[\\/:"*?<>|]+', '-', filename)

def add_keywords_and_job_title_to_pdf(path_pdf, keywords, job_title, output_path):
    try:
        doc = fitz.open(path_pdf)
        font_size = 8
        font_name = "helv"
        color = (0, 0, 0)
        total_pages = len(doc)
        total_keywords = len(keywords)
        keywords_per_page = total_keywords // total_pages + 1

        for page_num in range(total_pages):
            page = doc[page_num]
            rect = page.rect
            x = 0
            y = 0
            start = page_num * keywords_per_page
            end = start + keywords_per_page
            keywords_page = keywords[start:end]

            if not keywords_page and page_num != 0:
                continue

            words_per_line = 11
            lines = []

            if page_num == 0 and job_title and job_title != "Job title not found":
                lines.append(f"[{job_title}]")
                lines.append("")

            if keywords_page:
                keyword_lines = [" ".join(keywords_page[i:i + words_per_line]) for i in range(0, len(keywords_page), words_per_line)]
                lines.extend(keyword_lines)

            line_spacing = font_size - 5

            for index, line in enumerate(lines):
                if page_num == 0 and index == 0 and job_title and job_title != "Job title not found":
                    font_size_line = 16
                else:
                    font_size_line = font_size

                page.insert_text(
                    (x, y),
                    line,
                    fontname=font_name,
                    fontsize=font_size_line,
                    color=color,
                    overlay=False
                )
                y += line_spacing

        doc.save(output_path)
        doc.close()
        print(Fore.GREEN + f"\n✅ Optimized CV saved under: {output_path}\n")
    except Exception as e:
        print(Fore.RED + f"\n❌ An error occurred while modifying the PDF: {e}\n")

def scraper_linkedin(url, max_retries=5):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    session = requests.Session()
    session.headers.update(headers)
    retries = 0
    backoff = 1

    while retries < max_retries:
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                module_description = soup.find('div', class_='show-more-less-html__markup')
                if not module_description:
                    print(Fore.YELLOW + "⚠️ The module containing the job description was not found.\n")
                    description = ""
                else:
                    description = module_description.get_text(separator='\n', strip=True)

                module_title = soup.find('h1', class_='topcard__title')
                if not module_title:
                    h1 = soup.find('h1')
                    if h1:
                        job_title = h1.get_text(separator=' ', strip=True)
                        print(Fore.CYAN + f"Job title found: {job_title}\n")
                    else:
                        job_title = "Job title not found"
                        print(Fore.YELLOW + "⚠️ The job title was not found.\n")
                else:
                    job_title = module_title.get_text(separator=' ', strip=True)
                    print(Fore.CYAN + f"Job title found: {job_title}\n")

                return description, job_title

            elif response.status_code == 429:
                print(Fore.YELLOW + f"⚠️ Too many requests (429). Waiting for {backoff} seconds before retrying..." + Style.RESET_ALL)
                time.sleep(backoff)
                backoff *= 2
                retries += 1

            else:
                print(Fore.RED + f"\n❌ HTTP request error. Status: {response.status_code}\n")
                return None, None

        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"\n❌ HTTP request error: {e}\n")
            return None, None

    print(Fore.RED + "\n❌ Max retry attempts reached. Unable to retrieve the job posting content.\n")
    return None, None

def scraper_manual():
    print(Fore.BLUE + "\n📝 Manual Mode Activated.\n" + Style.RESET_ALL)
    print(Fore.CYAN + "🔍 Choose the method for entering the job description:" + Style.RESET_ALL)
    print(Fore.CYAN + "1. Direct input (press Ctrl+D to finish)" + Style.RESET_ALL)
    print(Fore.CYAN + "2. Use a temporary text editor" + Style.RESET_ALL)
    choice = input(Fore.CYAN + "🔗 Enter 1 or 2: " + Style.RESET_ALL).strip()

    if choice == '1':
        print(Fore.CYAN + "\n🔍 Enter the job description. Press Ctrl+D (EOF) on a new line to finish:" + Style.RESET_ALL)
        try:
            description = sys.stdin.read()
        except KeyboardInterrupt:
            print(Fore.RED + "\n❌ Input interrupted by user.\n")
            sys.exit(1)
    elif choice == '2':
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmpfile:
                tmpfile_path = tmpfile.name
                print(Fore.CYAN + "🔍 The text editor is now opening. Write or paste the job description, then save and close the editor." + Style.RESET_ALL)
                subprocess.call(['nano', tmpfile_path])  # Replace 'nano' with your preferred text editor if necessary
                tmpfile.seek(0)
                description = tmpfile.read()
        except KeyboardInterrupt:
            print(Fore.RED + "\n❌ Input interrupted by user.\n")
            sys.exit(1)
        finally:
            if os.path.exists(tmpfile_path):
                os.unlink(tmpfile_path)
    else:
        print(Fore.RED + "\n❌ Invalid choice. Please run the script again and choose 1 or 2.\n")
        sys.exit(1)

    try:
        job_title = input(Fore.CYAN + "🔍 Enter the job title: " + Style.RESET_ALL).strip()
    except KeyboardInterrupt:
        print(Fore.RED + "\n❌ Input interrupted by user.\n")
        sys.exit(1)

    return description, job_title

def main():
    parser = argparse.ArgumentParser(description="Optimize your CV with LinkedIn Keywords or Manual Mode.")
    parser.add_argument('-m', '--manual', action='store_true', help='Manual mode: provide job description and title manually.')
    args = parser.parse_args()

    print(Fore.YELLOW + """
@@@  @@@   @@@@@@    @@@@@@@  @@@  @@@  @@@@@@@   @@@@@@   
@@@  @@@  @@@@@@@@  @@@@@@@@  @@@  @@@  @@@@@@@  @@@@@@@   
@@!  @@@  @@!  @@@  !@@       @@!  !@@    @@!    !@@       
!@!  @!@  !@!  @!@  !@!       !@!  @!!    !@!    !@!       
@!@!@!@!  @!@!@!@!  !@!       @!@@!@!     @!!    !!@@!!    
!!!@!!!!  !!!@!!!!  !!!       !!@!!!      !!!     !!@!!!   
!!:  !!!  !!:  !!!  :!!       !!: :!!      !!:         !!:  
:!:  !:!  :!:  !:!  ::: :::   :!:  !:!      :!:        !!:!  
:: :!!:   :: :!!:   :: : :     ::   !!:     :: : : :  !!: : 
:   : :  :   :::  :   : :   :::  ::::  ::: :: :  : :  :   
""")
    if args.manual:
        description, job_title = scraper_manual()
    else:
        url = input(Fore.CYAN + "🔍 Enter the LinkedIn job posting URL: " + Style.RESET_ALL).strip()
        description, job_title = scraper_linkedin(url)

    if not description:
        print(Fore.RED + "\n❌ No description found. Exiting...\n")
        return

    keywords = extract_keywords(description)

    output_path = f"optimized_resume_{sanitize_filename(os.path.basename(RESUME_FILE))}"
    add_keywords_and_job_title_to_pdf(RESUME_FILE, keywords, job_title, output_path)

if __name__ == "__main__":
    main()
