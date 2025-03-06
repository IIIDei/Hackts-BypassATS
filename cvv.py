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

NOM_CV = ""     # Fill in your CV file name

def extraire_mots_cles(text, N=400):
    language = "fr"     # Set the language of the job posting; default is French ("fr")
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
    mots_cles = [kw for kw, score in keywords]
    return mots_cles

def sanitize_filename(filename):
    return re.sub(r'[\\/:"*?<>|]+', '-', filename)

def ajouter_mots_cles_et_titre_pdf(path_pdf, mots_cles, titre_poste, sortie_path):
    try:
        doc = fitz.open(path_pdf)
        font_size = 8
        font_name = "helv"
        couleur = (0, 0, 0)
        total_pages = len(doc)
        total_mots = len(mots_cles)
        mots_par_page = total_mots // total_pages + 1

        for page_num in range(total_pages):
            page = doc[page_num]
            rect = page.rect
            x = 0
            y = 0
            start = page_num * mots_par_page
            end = start + mots_par_page
            mots_page = mots_cles[start:end]

            if not mots_page and page_num != 0:
                continue

            mots_par_ligne = 11
            lignes = []

            if page_num == 0 and titre_poste and titre_poste != "Titre du poste non trouvé":
                lignes.append(f"[{titre_poste}]")
                lignes.append("")

            if mots_page:
                mots_lignes = [" ".join(mots_page[i:i + mots_par_ligne]) for i in range(0, len(mots_page), mots_par_ligne)]
                lignes.extend(mots_lignes)

            ligne_spacing = font_size - 5

            for index, ligne in enumerate(lignes):
                if page_num == 0 and index == 0 and titre_poste and titre_poste != "Titre du poste non trouvé":
                    font_size_line = 16
                else:
                    font_size_line = font_size

                page.insert_text(
                    (x, y),
                    ligne,
                    fontname=font_name,
                    fontsize=font_size_line,
                    color=couleur,
                    overlay=False
                )
                y += ligne_spacing

        doc.save(sortie_path)
        doc.close()
        print(Fore.GREEN + f"\n✅ CV optimisé sauvegardé sous : {sortie_path}\n")
    except Exception as e:
        print(Fore.RED + f"\n❌ Une erreur est survenue lors de la modification du PDF : {e}\n")

def scraper_offre_linkedin(url, max_retries=5):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9",
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
                    print(Fore.YELLOW + "⚠️ Le module contenant la description de l'annonce n'a pas été trouvé.\n")
                    description = ""
                else:
                    description = module_description.get_text(separator='\n', strip=True)

                module_titre = soup.find('h1', class_='topcard__title')
                if not module_titre:
                    h1 = soup.find('h1')
                    if h1:
                        titre_poste = h1.get_text(separator=' ', strip=True)
                        print(Fore.CYAN + f"Titre du poste trouvé : {titre_poste}\n")
                    else:
                        titre_poste = "Titre du poste non trouvé"
                        print(Fore.YELLOW + "⚠️ Le titre du poste n'a pas été trouvé.\n")
                else:
                    titre_poste = module_titre.get_text(separator=' ', strip=True)
                    print(Fore.CYAN + f"Titre du poste trouvé : {titre_poste}\n")

                return description, titre_poste

            elif response.status_code == 429:
                print(Fore.YELLOW + f"⚠️ Trop de requêtes (429). Attente de {backoff} secondes avant de réessayer..." + Style.RESET_ALL)
                time.sleep(backoff)
                backoff *= 2
                retries += 1

            else:
                print(Fore.RED + f"\n❌ Erreur lors de la requête HTTP. Statut : {response.status_code}\n")
                return None, None

        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"\n❌ Erreur lors de la requête HTTP : {e}\n")
            return None, None

    print(Fore.RED + "\n❌ Nombre maximal de tentatives atteint. Impossible de récupérer le contenu de l'annonce.\n")
    return None, None

def scraper_manuel():
    print(Fore.BLUE + "\n📝 Mode Manuel Activé.\n" + Style.RESET_ALL)
    print(Fore.CYAN + "🔍 Choisissez la méthode de saisie de la description de l'annonce :" + Style.RESET_ALL)
    print(Fore.CYAN + "1. Saisie directe (pressez Ctrl+D pour terminer)" + Style.RESET_ALL)
    print(Fore.CYAN + "2. Utiliser un éditeur de texte temporaire" + Style.RESET_ALL)
    choix = input(Fore.CYAN + "🔗 Entrez 1 ou 2 : " + Style.RESET_ALL).strip()

    if choix == '1':
        print(Fore.CYAN + "\n🔍 Entrez la description de l'annonce. Pressez Ctrl+D (EOF) sur une nouvelle ligne pour terminer la saisie :" + Style.RESET_ALL)
        try:
            description = sys.stdin.read()
        except KeyboardInterrupt:
            print(Fore.RED + "\n❌ Saisie interrompue par l'utilisateur.\n")
            sys.exit(1)
    elif choix == '2':
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmpfile:
                tmpfile_path = tmpfile.name
                print(Fore.CYAN + "🔍 L'éditeur de texte s'ouvre maintenant. Écrivez ou collez la description de l'annonce, puis sauvegardez et fermez l'éditeur." + Style.RESET_ALL)
                subprocess.call(['nano', tmpfile_path])  # Replace 'nano' with your preferred text editor if necessary
                tmpfile.seek(0)
                description = tmpfile.read()
        except KeyboardInterrupt:
            print(Fore.RED + "\n❌ Saisie interrompue par l'utilisateur.\n")
            sys.exit(1)
        finally:
            if os.path.exists(tmpfile_path):
                os.unlink(tmpfile_path)
    else:
        print(Fore.RED + "\n❌ Choix invalide. Veuillez exécuter à nouveau le script et choisir 1 ou 2.\n")
        sys.exit(1)

    try:
        titre_poste = input(Fore.CYAN + "🔍 Entrez le titre du poste : " + Style.RESET_ALL).strip()
    except KeyboardInterrupt:
        print(Fore.RED + "\n❌ Saisie interrompue par l'utilisateur.\n")
        sys.exit(1)

    return description, titre_poste

def main():
    parser = argparse.ArgumentParser(description="Optimisation de votre CV avec les Mots-Clés LinkedIn ou Mode Manuel.")
    parser.add_argument('-m', '--manuel', action='store_true', help='Mode manuel : fournir la description et le titre de l\'annonce manuellement.')
    args = parser.parse_args()

    print(Fore.YELLOW + """
@@@  @@@   @@@@@@    @@@@@@@  @@@  @@@  @@@@@@@   @@@@@@   
@@@  @@@  @@@@@@@@  @@@@@@@@  @@@  @@@  @@@@@@@  @@@@@@@   
@@!  @@@  @@!  @@@  !@@       @@!  !@@    @@!    !@@       
!@!  @!@  !@!  @!@  !@!       !@!  @!!    !@!    !@!       
@!@!@!@!  @!@!@!@!  !@!       @!@@!@!     @!!    !!@@!!    
!!!@!!!!  !!!@!!!!  !!!       !!@!!!      !!!     !!@!!!   
!!:  !!!  !!:  !!!  :!!       !!: :!!     !!:         !:!  
:!:  !:!  :!:  !:!  :!:       :!:  !:!    :!:        !:!   
::   :::  ::   :::   ::: :::   ::  :::     ::    :::: ::   
 :   : :   :   : :   :: :: :   :   :::     :     :: : :    
""" + Style.RESET_ALL)
    print(Fore.BLUE + Style.BRIGHT + "\n=== Optimisation de votre CV avec les Mots-Clés LinkedIn===\n\n(Fermez l'app en faisant CTRL + C)\n" + Style.RESET_ALL)

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path_pdf = os.path.join(script_dir, NOM_CV)
        if not os.path.isfile(path_pdf):
            print(Fore.RED + f"\n❌ Le fichier CV '{NOM_CV}' n'a pas été trouvé dans le répertoire {script_dir}.\n")
            return

        while True:
            if args.manuel:
                description, titre_poste = scraper_manuel()
            else:
                url_annonce = input(Fore.CYAN + "🔗 Entrez l'URL de l'annonce LinkedIn : " + Style.RESET_ALL).strip()
                if not url_annonce.startswith("https://www.linkedin.com/jobs/view/"):
                    print(Fore.RED + "\n❌ L'URL fournie ne semble pas être une URL d'annonce LinkedIn valide.\n")
                    continue
                print(Fore.BLUE + "\n🔍 Scraping de l'annonce LinkedIn..." + Style.RESET_ALL)
                description, titre_poste = scraper_offre_linkedin(url_annonce)
                if description is None and titre_poste is None:
                    print(Fore.RED + "❌ Impossible de récupérer le contenu de l'annonce.\n")
                    continue

            if description:
                mots_cles = extraire_mots_cles(description, N=400)
                print(Fore.GREEN + f"✅ Mots-clés extraits ({len(mots_cles)}): {', '.join(mots_cles[:20])}...\n" + Style.RESET_ALL)
            else:
                mots_cles = []
                print(Fore.YELLOW + "⚠️ Aucun mot-clé extrait car la description est vide.\n" + Style.RESET_ALL)

            if titre_poste and titre_poste != "Titre du poste non trouvé":
                print(Fore.GREEN + f"✅ Titre du poste extrait : {titre_poste}\n" + Style.RESET_ALL)
            else:
                titre_poste = "Titre du poste non trouvé"
                print(Fore.YELLOW + "⚠️ Aucun titre de poste trouvé.\n" + Style.RESET_ALL)

            if titre_poste != "Titre du poste non trouvé":
                titre_sanitized = sanitize_filename(titre_poste)
            else:
                titre_sanitized = "Titre_Poste"

            nom_fichier, extension = os.path.splitext(NOM_CV)
            sortie_nom = f"[{nom_fichier}] [{titre_sanitized}]{extension}"
            sortie_path = os.path.join(script_dir, sortie_nom)

            ajouter_mots_cles_et_titre_pdf(path_pdf, mots_cles, titre_poste, sortie_path)

            print(Fore.BLUE + "🎉 Processus terminé avec succès !" + Style.RESET_ALL + "\n")
            print(Fore.CYAN + "----------------------------------------\n" + Style.RESET_ALL)
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n❌ Application fermée (Ctrl+C).\n" + Style.RESET_ALL)
        sys.exit(1)

if __name__ == "__main__":
    main()
