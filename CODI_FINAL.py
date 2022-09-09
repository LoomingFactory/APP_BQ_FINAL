import streamlit as st
from streamlit_option_menu import option_menu

from datetime import datetime
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

def dt_to_ts(data_str):
    dt = datetime.strptime(data_str, '%Y-%m-%d')
    ts=int(round(dt.timestamp()))*1000
    return ts

def ts_to_dt(temps):
  dt_object = datetime.fromtimestamp(temps/1000)
  data = dt_object.strftime("%Y-%m-%d")
  return data


def ax_despres_login():
    if usuari != st.secrets["login"]["usuari"] or contra != st.secrets["login"]["contra"]:
        st.error('Usuari i/o contrasenya erronies')
    elif usuari == st.secrets["login"]["usuari"] and contra == st.secrets["login"]["contra"]:
        #st.balloons()
        st.session_state['pagina'] = 'dins_app'


# si no te cap directori predeterminat encara
if 'op_fitxer' not in st.session_state:
	st.session_state['op_fitxer'] = {'dir':"","nom_fitxer_energies_de_eines":"log_energies_de_eines","nom_fitxer_energies":"log_energies","nom_fitxer_eines":"log_eines"}


# li dic que comenci amb la pagina de login
if 'pagina' not in st.session_state:
	st.session_state['pagina'] = 'login'

# li dic que comenci amb la pagina de buscar (introduir dades de cerca)
if 'buscar' not in st.session_state:
	st.session_state['buscar'] = True

################################################    
#################### LOG IN ####################
################################################

if st.session_state['pagina'] == 'login':
    st.title("HAAS DB")
    st.write("@CIM UPC")

    with st.sidebar:
        usuari = st.text_input('Usuari: ')
        contra = st.text_input('Contrasenya: ',type = 'password')
        boto_login = st.button('login', on_click = ax_despres_login) #aixi refresco la pagina i ja estare a dins de la app

    
##################################################
#################### DINS APP ####################
##################################################

elif st.session_state['pagina'] == 'dins_app':

    ##################################################
    #################### SIDEBAR #####################
    ##################################################

    with st.sidebar:      
        
        
        guardar_dades = st.checkbox('Guardar dades automàticament',value=True)
        
        if guardar_dades:
            with st.expander("Opcions desament dades"):
                directori = st.text_input("Directori on guardar. Ex: C:\\looming\\data")
                if st.session_state['op_fitxer']['nom_fitxer_eines'] != "":
                    nom_fitxer_eines = st.text_input("Nom fitxer eines. Ex:log_eines",value = st.session_state['op_fitxer']['nom_fitxer_eines'])

                if st.session_state['op_fitxer']['nom_fitxer_energies'] != "":
                    nom_fitxer_energies = st.text_input("Nom fitxer eines. Ex:log_energies",value = st.session_state['op_fitxer']['nom_fitxer_energies'])

                if st.session_state['op_fitxer']['nom_fitxer_energies_de_eines'] != "":
                    nom_fitxer_energies_de_eines = st.text_input("Nom fitxer eines. Ex:log_energies_de_eines",value = st.session_state['op_fitxer']['nom_fitxer_energies_de_eines'])

                st.session_state['op_fitxer']['dir'] = directori
                st.session_state['op_fitxer']['nom_fitxer_eines'] = nom_fitxer_eines
                st.session_state['op_fitxer']['nom_fitxer_energies'] = nom_fitxer_energies
                st.session_state['op_fitxer']['nom_fitxer_energies_de_eines'] = nom_fitxer_energies_de_eines



        st.write('')

        # icones a https://icons.getbootstrap.com/
        opcio_dates = option_menu(menu_title = 'Buscar per dates', options= ["Interval", "Relatiu"] , icons= ["calendar-week", "stopwatch"], menu_icon= "calendar-plus", orientation= "horizontal")

        if opcio_dates == "Interval":
            di_dtt = st.date_input("Data inici") 
            df_dtt= st.date_input("Data fi") 
            di = dt_to_ts(str(di_dtt))
            df = dt_to_ts(str(df_dtt))

            lower_than= df
            greater_than = di

            st.write('   ')  

        elif opcio_dates == "Relatiu":

            op_timestamp = [604800000, 1209600000, 2592000000, 5184000000]
            op = ['1 setmana','2 setmanes', '1 mes', '2 mesos']
            opcions = st.selectbox('Des de fa: ', op)

            dara_dtt = datetime.now()
            dara = round(datetime.timestamp(dara_dtt)*1000)

            drel = dara - op_timestamp[op.index(opcions)]

            drel_dtt = ts_to_dt(drel)
            st.write('   ', drel_dtt)

            lower_than=  dara #1643197403000 #
            greater_than = drel #1643194196000  #

            st.session_state['interval'] = [lower_than,greater_than]

            st.write('   ')
            st.write('   ')  
            st.write('   ')  
            st.write('   ')  

        if st.session_state['op_fitxer']['dir'] == "" and guardar_dades == True:
            st.warning("Falta posar-hi el directori on guardar les dades")

        MOSTRAR_DB = st.button('Mostrar DB')


    ##################################################
    #################### PRINCIPAL ###################
    ##################################################
    st.title('Resultats de la cerca')
    st.write("Aquí es mostraran la base de dades de EINES i ENERGIES per l'interval seleccionat, ademés de la DB de ENERGIES en el període restringit a les dades de EINES anteriors")

 

    if MOSTRAR_DB:

        ############################### CONNECT TO BIGQUERY: Uses st.experimental_singleton to only run once ##################################
        # Create API client.
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = bigquery.Client(credentials=credentials)

        # Perform query.
        # Uses st.experimental_memo to only rerun when the query changes or after ttl time --> 10 min. = 60seg*10 = 600
        @st.experimental_memo(ttl=600)
        def run_query_eines(query):
            query_job = client.query(query)
            rows_raw = query_job.result()
            rows = [dict(row) for row in rows_raw] # Convert to list of dicts. Required for st.experimental_memo to hash the return value.
            df = pd.DataFrame(rows)
            return df

        @st.experimental_memo(ttl=600)
        def run_query_energies(query):
            query_job = client.query(query)
            rows_raw = query_job.result()
            rows = [dict(row) for row in rows_raw] 
            df = pd.DataFrame(rows)
            return df

        @st.experimental_memo(ttl=600)
        def run_query_eines_energies(query):
            query_job = client.query(query)
            rows_raw = query_job.result()
            rows = [dict(row) for row in rows_raw] 
            df = pd.DataFrame(rows)
            return df

        ########################################## 1. EINES ##########################################

        st.title('1. DB EINES')
        query = """
            select  * from `prova-insertar-taules.dades_CIM.logs_eines` 
            WHERE TIMESTAMP between {0} AND {1}
            UNION ALL
            select  * from `prova-insertar-taules.realtime_CIM.eines` 
            WHERE TIMESTAMP between {2} AND {3}
            ORDER BY TIMESTAMP ASC 
        """.format(greater_than,lower_than,greater_than,lower_than)

        df_eines = run_query_eines(query)
        cols = df_eines.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        df_eines = df_eines[cols] 

        if not df_eines.empty:
            st.write('Rows :', df_eines.shape[0])
            st.dataframe(df_eines)

            max_timestamp = int(df_eines['TIMESTAMP'].max())
            min_timestamp = int(df_eines['TIMESTAMP'].min())

            #descargable_eines = df_eines.to_csv().encode('utf-8')
            #st.download_button("Descarregar DB EINES",descargable_eines,"resultao.csv","text/csv",key='download-csv-eines')

            if guardar_dades:
                
                nom = str(st.session_state['op_fitxer']['dir'])+"\\"+st.session_state['op_fitxer']['nom_fitxer_eines']+".csv"
                df_eines.to_csv(nom, header=True, index=False)


        else:
            st.write("No hi ha dades d'eines per aquest període")

        ########################################## 2. ENERGIES ##########################################

        st.title('2. DB ENERGIES')
        query = """
            SELECT * from `prova-insertar-taules.dades_CIM.logs_energy1` 
            WHERE TIMESTAMP between {0} AND {1}
            UNION ALL
            SELECT * from `prova-insertar-taules.dades_CIM.logs_energy2` 
            WHERE TIMESTAMP between {2} AND {3}
            UNION ALL
            SELECT * from `prova-insertar-taules.realtime_CIM.energies` 
            WHERE TIMESTAMP between {4} AND {5}
            ORDER BY TIMESTAMP ASC 
        """.format(greater_than,lower_than,greater_than,lower_than,greater_than,lower_than)

        df_energia = run_query_energies(query)

        if not df_energia.empty:
            st.write('Rows :', df_energia.shape[0])
            st.dataframe(df_energia)
            #descargable_energies = df_energia.to_csv().encode('utf-8')
            #st.download_button("Descarregar DB ENERGIES",descargable_energies,"resultao.csv","text/csv",key='download-csv-energies')

            if guardar_dades:
                nom = str(st.session_state['op_fitxer']['dir'])+"\\"+st.session_state['op_fitxer']['nom_fitxer_energies']+".csv"
                df_energia.to_csv(nom, header=True, index=False)

        else:
            st.write("No hi ha dades d'energies per aquest període")


        ########################################## 3. ENERGIES pertanyent a EINES ##########################################

        st.title('3. DB ENERGIES pertanyent a eines')

        if not df_eines.empty: 

            if not df_energia.empty:

                query = """
                    SELECT * from `prova-insertar-taules.dades_CIM.logs_energy1` 
                    WHERE TIMESTAMP between {0} AND {1}
                    UNION ALL
                    SELECT * from `prova-insertar-taules.dades_CIM.logs_energy2` 
                    WHERE TIMESTAMP between {2} AND {3}
                    UNION ALL
                    SELECT * from `prova-insertar-taules.realtime_CIM.energies` 
                    WHERE TIMESTAMP between {4} AND {5}
                    ORDER BY TIMESTAMP ASC 
                """.format(min_timestamp,max_timestamp,min_timestamp,max_timestamp,min_timestamp,max_timestamp)

                df_energia_de_eines = run_query_eines_energies(query)

                st.write('Rows :', df_energia_de_eines.shape[0])
                st.dataframe(df_energia_de_eines)

                if not df_energia_de_eines.empty:
                    #descargable_energies_eines = df_energia_de_eines.to_csv().encode('utf-8')
                    #st.download_button("Descarregar DB ENERGIES d'eines",descargable_energies_eines,"resultao.csv","text/csv",key='download-csv-energies-i-eines')

                    if guardar_dades:
                        nom = str(st.session_state['op_fitxer']['dir'])+"\\"+st.session_state['op_fitxer']['nom_fitxer_energies_de_eines']+".csv"
                        df_energia_de_eines.to_csv(nom, header=True, index=False)
                        st.balloons()
                
            else:
                st.write("No hi ha dades d'energies per aquest període")

        else:
            if df_energia.empty:
                st.write("No hi ha dades d'eines ni d'energies per aquest període")
            else:
                st.write("No hi ha dades d'eines per aquest període")
