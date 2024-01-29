import requests
from bs4 import BeautifulSoup as soup
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import matplotlib.pyplot as plt
import seaborn as sns
import time
import re

def clean_fbref(df):
    df.columns = df.columns.droplevel(0)
    df.drop(df[df['Pos.'] == 'Pos.'].index, inplace = True)
    df= df[["Giocatore","Ruolo","Nazione","Età","Nato","Squadra","PG","Tit","Min","Reti","Assist","Amm.","Esp."]]
    df.columns=["Giocatori","Ruolo","Nazione","Eta","Nato","Squadra","Presenze","Tit","Minuti giocati","Reti","Reti_per_90","Assist","Assist_per_90","Amm.","Esp."]
    df = df.drop(columns=["Reti_per_90","Assist_per_90"])
    df.dropna(subset=['Eta'], inplace=True)
    #df["Eta"]=df["Eta"].astype(int)
    df.fillna(0,inplace=True)
    df[["Minuti giocati","Eta","Nato","Tit","Reti","Assist","Presenze","Amm.","Esp."]]=df[["Minuti giocati","Eta","Nato","Tit","Reti","Assist","Presenze","Amm.","Esp."]].astype(int)
    #df["Reti_per_90"]=df["Reti_per_90"].str.replace(",",".").astype(float)
    #df["Assist_per_90"]=df["Assist_per_90"].str.replace(",",".").astype(float)
    df=df[df["Eta"]<21].sort_values(by=['Minuti giocati'],ascending=False)
    df.reset_index(inplace=True,drop=True)
    df["Nazione"]=df["Nazione"].str.split(" ").str[1]
    #convert presenze in int
    return df

def get_fbref():
    """Function to get data from FBref"""
    base_url = 'https://fbref.com/it/comp/11/'
    current_year = 2022

    # Define the number of years you want to subtract
    years_to_subtract = 34

    for i in range(years_to_subtract):
        # Calculate the year to use in the URL
        year_url = f"{current_year - i}-{current_year + 1 - i}"
        full_url = f'{base_url}{year_url}/stats/Statistiche-di-Serie-A-{year_url}'
        
        # Fetch data from the URL here
        data_players=pd.read_html(requests.get(full_url).text.replace('<!--','').replace('-->','')
        ,attrs={'id':'stats_standard'},thousands='.'
        )[0]
        data_players=clean_fbref(data_players)
        data_players.to_excel(f"SerieA{year_url}-Under21.xlsx",index=False)


def get_2_squadre(season,headers,url_name):
    url = f"https://www.transfermarkt.it{url_name}"
    r= requests.get(url, headers=headers)
    r.status_code  

    soups = soup(r.text, 'html.parser')  # r.content 대신 r.text도 가능
    player_info= soups.find_all('table', class_=['items'])
    player_info_odd_even= soups.find_all('tr', class_=['odd', 'even'])
    #player_info
    squadrta=[]
    minuti=[]
    for info in player_info_odd_even:
        player = info.find_all("td")
        #print(int(player[8].text.replace('-','0').replace("'","").replace('.','')))
        if (player[0].text)==season[2:4]+"/"+season[7:]:
            squadrta.append(player[3].img['alt'])
            #squadrta.append(re.search(r'\/(.*?)\/', player[3].a['href']).group(1))
            minuti.append(int(player[8].text.replace('-','0').replace("'","").replace('.','')))
    #stampa i due array creati
    if minuti[0]>minuti[1]:
        return(squadrta[0])
    else:
        return(squadrta[1])


def get_data_transfermarkt(url_base,headers,last_page,season):
    name=[]
    position=[]
    age=[]
    nation=[]
    team=[]
    presenze=[]
    cambio=[]
    mins=[]
    reti=[]

    for i in range(1, last_page+1):

        url = f"{url_base}&page={i}"
        r= requests.get(url, headers=headers)
        r.status_code  

        soups = soup(r.text, 'html.parser')  # r.content 대신 r.text도 가능
        player_info= soups.find_all('tr', class_=['odd', 'even'])

        # player_info에서 'td'태그만 모두 찾기
        for info in player_info:
            player = info.find_all("td")

            name.append(player[3].text.replace("\n",""))
            position.append(player[4].text)
            age.append(player[6].text)
            if player[7].text == "2 Squadre":
                #team.append(player[7].text)
                team.append(get_2_squadre(season,headers,player[7].find("a").get("href")))
                #player[7].find("a").get("href")
            else:
                team.append(player[7].img['alt'])
                #team.append(re.search(r'\/(.*?)\/', player[7].a['href']).group(1))
            img_tags = player[5].find_all("img")
            if len(img_tags) >= 2:
                nation.append(f"{img_tags[0]['alt']}/{img_tags[1]['alt']}")
            else:
                nation.append(player[5].img['alt'])
            presenze.append(player[8].text)
            cambio.append(player[9].text)
            mins.append(int(player[11].text.replace(".","")))
            reti.append(player[12].text)
        
        time.sleep(1)

        # pd.DataFrame()으로 저장하기

    giocatori = pd.DataFrame(
            {
            "Giocatori":name,
            "Ruolo":position,
            "age":age,
            "Nazione":nation,
            "Squadra":team,
            "Presenze":presenze,
            "Cambio":cambio,
            "Minuti giocati":mins,
            "Reti":reti
            }
        )

    #split the column Nasc./Età in two columns
    giocatori["Nato"]=giocatori["age"].str.split(" ").str[0]
    giocatori["Eta"]=giocatori["age"].str.split(" ").str[1]
    #chech if there is a † in the column Eta
    giocatori["Eta"]=giocatori["Eta"].str.replace("†","")

    giocatori["Eta"]=giocatori["Eta"].str.replace("(","").str.replace(")","").astype(int)
    giocatori["Reti"]=giocatori["Reti"].replace("-","0").astype(int)
    giocatori["Cambio"]=giocatori["Cambio"].replace("-","0").astype(int)
    giocatori["Presenze"]=giocatori["Presenze"].replace("-","0").astype(int)
    
    #giocatori["Minuti giocati"]=giocatori["Minuti giocati"].replace(".",",").astype(int)

    giocatori.drop(columns=["age"],inplace=True)   
    return giocatori

def get_transfermarkt(current_year,years_to_subtract):
    """Function to get data of under 21 player of Serie a from Transfermarkt"""
    #current_year = 2022

    # Define the number of years you want to subtract
    #years_to_subtract = 54
    headers = {'User-Agent': 
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
    for i in range(years_to_subtract):
        # Calculate the year to use in the URL
        year_url = f"{current_year - i}"
        season=f"{current_year - i}-{current_year + 1 - i}"
        url = f"https://www.transfermarkt.it/serie-a/dauerbrenner/wettbewerb/IT1/plus/1/galerie/0?saison_id={year_url}&pos=&detailpos=&altersklasse=u20"
        #url=f"https://www.transfermarkt.it/premier-league/dauerbrenner/wettbewerb/GB1/plus/1/galerie/0?saison_id={year_url}&pos=&detailpos=&altersklasse=u20"
        #url=f"https://www.transfermarkt.it/serie-b/dauerbrenner/wettbewerb/IT2/plus/1/galerie/0?saison_id={year_url}&pos=&detailpos=&altersklasse=u20"
        r= requests.get(url, headers=headers)
        parse = soup(r.text, 'html.parser') 
        pages=parse.find_all("li",class_="tm-pagination__list-item tm-pagination__list-item--icon-last-page")
        last_page=int(pages[0].find("a",class_="tm-pagination__link").get("href")[-1])
        data_players=get_data_transfermarkt(url,headers,last_page,season)
        data_players.to_excel(fr"C:\Users\franc\Documents\Progetto_Calciatori_Under21\transfermarkt\SerieA{season}-Under21.xlsx",index=False)
        #data_players.to_excel(fr"C:\Users\franc\Documents\Progetto_Calciatori_Under21\SerieB\B{season}-Under21.xlsx",index=False)



def get_uefa_ranking():
    base_url="https://kassiesa.net/uefa/data/"
    mylist=["method1/crank1998.html","method2/crank2003.html","method3/crank2008.html","method4/crank2013.html","method5/crank2018.html","method5/crank2023.html"]
    df=pd.DataFrame(columns=['stagione','valore'])
    i=0
    for objec in mylist:
        full_url = f'{base_url}{objec}'
        data_players=pd.read_html(requests.get(full_url).text.replace('<!--','').replace('-->','')
                ,attrs={'class':'t1'},thousands=',')[0]
        #data_players=data_players[data_players['country']=='Italy']
        data_players=data_players[data_players['country']=='Italy'].drop(["#","Unnamed: 1","country","ranking","teams"],axis=1)/data_players[0:20].drop(["#","Unnamed: 1","country","ranking","teams"],axis=1).sum()*100
        #drop the first and second column
        #data_players=data_players.drop(["#","Unnamed: 1","country","ranking","teams"],axis=1)
        
        new_df = data_players.T.reset_index()
        new_df.columns = ['stagione', 'valore']
        df=pd.concat([df,new_df]).reset_index(drop=True)

    current_year = 1968
    years_to_subtract = 1998
    dataframe=pd.DataFrame(columns=['stagione','valore'])
    for i in range(current_year,years_to_subtract,5): 
        full_url = f'{base_url}method1/crank{i}.html'
        data_players=pd.read_html(requests.get(full_url).text.replace('<!--','').replace('-->','')
                ,attrs={'class':'t1'},thousands=',')[0]
        #data_players=data_players[data_players['country']=='Italy']
        #data_players=data_players.drop(["#","Unnamed: 1","country","ranking","teams"],axis=1)
        data_players=data_players[data_players['country']=='Italy'].drop(["#","Unnamed: 1","country","ranking","teams"],axis=1)/data_players[0:20].drop(["#","Unnamed: 1","country","ranking","teams"],axis=1).sum()*100
        new_df = data_players.T.reset_index()
        new_df.columns = ['stagione', 'valore']
        dataframe=pd.concat([dataframe,new_df]).reset_index(drop=True)

    uefa_ranking=pd.concat([dataframe,df]).reset_index(drop=True)
    uefa_ranking['stagione'][0:37]=uefa_ranking['stagione'][0:37].astype(str).str[:2].astype(int)+1900
    uefa_ranking['stagione'][37:]=uefa_ranking['stagione'][37:].astype(str).str[:2].astype(int)+2000
    #drop the first row
    uefa_ranking=uefa_ranking.iloc[1:]
    uefa_ranking.set_index('stagione',inplace=True)
    uefa_ranking.index.name = None
    #rename valore column in Uefa_Ranking and convert it in int
    uefa_ranking.rename(columns={'valore':'Uefa_Ranking'},inplace=True)
    uefa_ranking['Uefa_Ranking']=uefa_ranking['Uefa_Ranking'].astype(float)
    return uefa_ranking

def get_table_result():
    base_url = f"https://www.transfermarkt.it/serie-a/tabelle/wettbewerb/IT1?saison_id="
    current_year = 2022

    # Define the number of years you want to subtract
    years_to_subtract = 56

    for i in range(years_to_subtract):
        # Calculate the year to use in the URL
        
        full_url = f'{base_url}{current_year-i}'
        headers = {'User-Agent': 
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
        

        r= requests.get(full_url, headers=headers)
        r.status_code  

        soups = soup(r.text, 'html.parser')  # r.content 대신 r.text도 가능
        player_info_odd_even= soups.find(id="yw1").find("tbody").find_all("tr")

        squadra=[]
        posizione=[]
        for info in player_info_odd_even:
            player = info.find_all("td")
            #print(player)
            squadra.append(player[1].img['alt'])
            #squadra.append(re.search(r'\/(.*?)\/', player[1].a['href']).group(1))
            posizione.append(int(player[0].text))
        
        giocatori = pd.DataFrame(
                    {
                    "Posizione":posizione,
                    "Squadra":squadra,
                    }
                )

        #giocatori.head(20)
        giocatori.to_excel(fr"C:\Users\franc\Documents\Progetto_Calciatori_Under21\classifica\Classifica_{current_year-i}-{current_year + 1 - i}.xlsx",index=False)