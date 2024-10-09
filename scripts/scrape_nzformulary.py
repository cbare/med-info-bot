"""
Scrape medication names and brochure links from the New Zealand Formulary website.
"""
import requests
from bs4 import BeautifulSoup


# Step 1: Accept terms and conditions
def accept_terms_and_conditions(session, url):
    form_url = url + "/home/licence"  # URL where the form is submitted
    form_data = {"btnAcceptTermsAndConditions": "Accept"}  # Form data for submission
    session.post(form_url, data=form_data)


# Function to scrape the medication names and brochure links
def scrape_medication_data(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Finding the section that contains medications and brochures
    medications = []
    for med in soup.find_all('p'):
        med_name = next(med.stripped_strings)
        if len(med_name) == 1: continue
        links = med.find_all('a')
        link_urls = {
            link.text.strip():link.get('href')
            for link in links
        } if links else {}
        medications.append(
            {
                "medication": med_name,
                "links": link_urls,
            }
        )
    
    return {
        "medications": medications,
    }

# this didn't work, can't get past the terms and conditions
url = "https://nzf.org.nz/nzf_70421"
with requests.Session() as session:
    # Step 1: Accept terms and conditions
    accept_terms_and_conditions(session, url)

    # Step 2: Scrape data after accepting terms
    response = session.get(url)
    response.raise_for_status()
    html = response.text


# luckily, view source works
with open('data/nzformulary-index.html', 'rt') as f:
    html = f.read()


medication_data = scrape_medication_data(html)

# Print scraped data
for med_name, brochure_link in medication_data:
    print(f"Medication: {med_name}, Brochure: {brochure_link}")
