import requests
from bs4 import BeautifulSoup
import json
from app import app, db
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel
import schedule
import time
import datetime
from shutil import copyfile
import os 

def getCatswebClasses(terms, seasons, years):

    c = requests.Session()

    # Get cookie from the login page
    url = 'https://ssb.txstate.edu/prod/twbkwbis.P_WWWLogin'
    c.get(url)

    # Open catsweb credentials file
    catsweb_credentials = json.load(open("catsweb_credentials.json", "r"))

    # Supply username and password from credentials file
    payload = {
        "sid": catsweb_credentials["sid"],
        "PIN": catsweb_credentials["PIN"] 
    }

    # Give headers to make it seem like we're not a robot
    headers = {
        "Host": "ssb.txstate.edu",
        "Connection": "keep-alive",
        "Content-Length": "27",
        "Cache-Control": "max-age=0",
        "Origin": "https://ssb.txstate.edu",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://ssb.txstate.edu/prod/twbkwbis.P_WWWLogin",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Make a POST request to the validation login page with the headers and payload
    validate_url = 'https://ssb.txstate.edu/prod/twbkwbis.P_ValLogin'
    c.post(validate_url, headers=headers, data=payload)

    for i in range(len(terms)):

        print("Updating classes for {}, {}".format(seasons[i], years[i]))

        # Make a request to this link to get a list of all the classes offered at Texas State
        print("TERM: ", terms[i])
        classes_url = "https://ssb.txstate.edu/prod/bwskfcls.P_GetCrse_Advanced?rsts=dummy&crn=dummy&term_in={}&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_subj=ACC&sel_subj=ADED&sel_subj=A+S&sel_subj=AAS&sel_subj=AGED&sel_subj=AG&sel_subj=ASL&sel_subj=ANTH&sel_subj=ARAB&sel_subj=ART&sel_subj=ARTF&sel_subj=ARTH&sel_subj=ARTS&sel_subj=ARTT&sel_subj=AT&sel_subj=BILG&sel_subj=BIO&sel_subj=B+A&sel_subj=BLAW&sel_subj=CTE&sel_subj=CHEM&sel_subj=CHI&sel_subj=CE&sel_subj=CLS&sel_subj=ARTC&sel_subj=CDIS&sel_subj=COMM&sel_subj=CIS&sel_subj=CS&sel_subj=CIM&sel_subj=CSM&sel_subj=CA&sel_subj=COUN&sel_subj=CJ&sel_subj=CI&sel_subj=DAN&sel_subj=DE&sel_subj=DVST&sel_subj=ESLL&sel_subj=ESLR&sel_subj=ESLS&sel_subj=ESLW&sel_subj=ECE&sel_subj=ECO&sel_subj=ED&sel_subj=EDST&sel_subj=EDCL&sel_subj=EDP&sel_subj=EDTC&sel_subj=EE&sel_subj=ENGR&sel_subj=ENG&sel_subj=ESS&sel_subj=FCD&sel_subj=FCS&sel_subj=FM&sel_subj=FIN&sel_subj=FR&sel_subj=GS&sel_subj=GNST&sel_subj=GEO&sel_subj=GEOL&sel_subj=GER&sel_subj=HIM&sel_subj=HP&sel_subj=HS&sel_subj=HA&sel_subj=HIST&sel_subj=HON&sel_subj=IE&sel_subj=ID&sel_subj=IS&sel_subj=ITAL&sel_subj=JAPA&sel_subj=LATS&sel_subj=LS&sel_subj=LING&sel_subj=LTCA&sel_subj=MGT&sel_subj=MFGE&sel_subj=MKT&sel_subj=MC&sel_subj=MATH&sel_subj=MSEC&sel_subj=MCS&sel_subj=MS&sel_subj=MODL&sel_subj=MU&sel_subj=MUSE&sel_subj=MUSP&sel_subj=NCBM&sel_subj=NCBW&sel_subj=NHT&sel_subj=NURS&sel_subj=NUTR&sel_subj=OCED&sel_subj=PHIL&sel_subj=PFW&sel_subj=PT&sel_subj=PHYS&sel_subj=POSI&sel_subj=PS&sel_subj=PSY&sel_subj=PA&sel_subj=PH&sel_subj=QMST&sel_subj=RTT&sel_subj=RDG&sel_subj=REC&sel_subj=REL&sel_subj=RC&sel_subj=RUSS&sel_subj=SPSY&sel_subj=SOWK&sel_subj=SOCI&sel_subj=SPAN&sel_subj=SPED&sel_subj=SAHE&sel_subj=SUST&sel_subj=TECH&sel_subj=GC&sel_subj=TH&sel_subj=US&sel_subj=WS&sel_crse=&sel_title=&sel_schd=%25&sel_insm=%25&sel_from_cred=&sel_to_cred=&sel_camp=%25&sel_levl=%25&sel_ptrm=%25&sel_instr=%25&sel_sess=%25&sel_attr=%25&begin_hh=0&begin_mi=0&begin_ap=a&end_hh=0&end_mi=0&end_ap=a&SUB_BTN=Section+Search&path=1".format(terms[i])

        response = c.get(classes_url)

        # Parse response into BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        all_classes = []
        individual_class = {}
        index = 1

        for td in soup.findAll('td', {'class': 'dddefault'}):
            if index is 1:
                individual_class["closed_status"] = td.text.strip()
                index = index + 1
                continue
            if index is 2:
                individual_class["CRN"] = td.text.strip()
                index = index + 1
                continue
            if index is 3:
                individual_class["department"] = td.text.strip()
                index = index + 1
                continue
            if index is 4:
                individual_class["class_number"] = td.text.strip()
                index = index + 1
                continue
            if index is 5:
                individual_class["class_section"] = td.text.strip()
                index = index + 1
                continue
            if index is 6:
                individual_class["campus"] = td.text.strip()
                index = index + 1
                continue
            if index is 7:
                individual_class["credit_hours"] = td.text.strip()
                index = index + 1
                continue
            if index is 8:
                individual_class["class_name"] = td.text.strip()
                index = index + 1
                continue
            if index is 9:
                individual_class["days"] = td.text.strip()
                index = index + 1
                continue
            if index is 10:
                individual_class["time"] = td.text.strip()
                index = index + 1
                continue
            if index is 11:
                individual_class["cap"] = td.text.strip()
                index = index + 1
                continue
            if index is 12:
                individual_class["act"] = td.text.strip()
                index = index + 1
                continue
            if index is 13:
                individual_class["rem"] = td.text.strip()
                index = index + 1
                continue
            if index is 14:
                individual_class["wl_cap"] = td.text.strip()
                index = index + 1
                continue
            if index is 15:
                individual_class["wl_act"] = td.text.strip()
                index = index + 1
                continue
            if index is 16:
                individual_class["wl_rem"] = td.text.strip()
                index = index + 1
                continue
            if index is 17:
                individual_class["instructor"] = td.text.strip()
                index = index + 1
                continue
            if index is 18:
                individual_class["date"] = td.text.strip()
                index = index + 1
                continue
            if index is 19:
                individual_class["location"] = td.text.strip()
                index = index + 1
                continue
            if index is 20:
                individual_class["attribute"] = td.text.strip()
                index = 1
                all_classes.append(individual_class)
                individual_class = {}
                continue

        classes = ClassModel.query.filter_by(season = seasons[i], year = years[i])

        for university_class in classes:

            for scraped_class in all_classes:
                if str(university_class.class_number) == scraped_class["class_number"] and str(university_class.class_section) == scraped_class["class_section"] and university_class.department == scraped_class["department"]:
                    # Update the instructor name
                    university_class.professor = scraped_class["instructor"].replace('(P)', '')

                    # Update the location of the class
                    university_class.class_location = scraped_class["location"]

                    # Update the number of enrolled students in the class
                    university_class.num_enrolled_students = int(scraped_class["act"])

                    # Update the days that this class takes place in
                    university_class.days = scraped_class["days"]

                    # Update the time that the class takes place in
                    university_class.class_time = scraped_class["time"]

                    # Update the potentially enrolled students 
                    unregistered = 0

                    for override in university_class.overrides:
                        if override.registration_status == False:
                            unregistered = unregistered + 1
                    
                    university_class.potentially_enrolled_students = int(scraped_class["act"]) + unregistered

                    university_class.percentage_filled = university_class.potentially_enrolled_students / university_class.max_capacity

                    break
        
        db.session.commit()

def backupDatabase():
    copyfile(os.getcwd() + '/app.db', os.getcwd() + '/database_backups/app_backup.db')

def updateClasses():
    # Get the current date
    today = datetime.date.today()

    # If between January and May
    if today.month <= 5:
        try:
            getCatswebClasses(terms = [ str(today.year) + '30', str(today.year) + '50', str(today.year + 1) + '10'], seasons = ['Spring', 'Summer', 'Fall'], years = [today.year, today.year, today.year])
            backupDatabase()
        except:
            pass
    # If between June and August
    elif today.month > 5 and today.month <= 8:
        try:
            getCatswebClasses(terms = [ str(today.year) + '50', str(today.year + 1) + '10', str(today.year) + '30'], seasons = ['Summer', 'Fall', 'Spring'], years = [today.year, today.year, today.year + 1])
            backupDatabase()
        except:
            pass

    # If between September and December
    else:
        try:
            getCatswebClasses(terms = [ str(today.year + 1) + '10', str(today.year) + '30', str(today.year) + '50'], seasons = ['Fall', 'Spring', 'Summer'], years = [today.year, today.year + 1, today.year + 1])
            backupDatabase()
        except:
            pass

if __name__ == "__main__":

    backupDatabase()

    updateClasses()

    schedule.every(2).minutes.do(updateClasses)

    while True: 
        schedule.run_pending() 
        time.sleep(1) 