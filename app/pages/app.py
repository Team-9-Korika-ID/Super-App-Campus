import streamlit as st
from PyPDF2 import PdfReader
import zipfile
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
import seaborn as sns
from sentence_transformers import SentenceTransformer, util
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
left_column, right_column = st.columns(2)

# Input kiri
with left_column:
    st.header("Input")
    st.info('Datasets and reports older than 30 days may be deleted from our server to save space. You can always delete the data yourself.')
    uploaded_files = st.file_uploader("Upload file (zip/PDF)", type=["zip", "pdf"], accept_multiple_files=True)
    judul_database = st.text_input('Masukkan Judul Database (* Wajib)')
    # st.multiselect('Multiselect', ['a', 'b', 'c'])
    st.write('When you upload a dataset, it will be analyzed on our server. Only you and the people you share the report with will be able to view the analysis results.')
    st.checkbox('I accept the terms and conditions')

# Output kanan
with right_column:
    st.header("Output")
    # Tampilkan informasi file jika file telah diunggah
    if uploaded_files is not None:
        df_files_info = pd.DataFrame(columns=["NRP", "Nama siswa", "Tipe file", "File size (bytes)"])
        for uploaded_file in uploaded_files:
            # Informasi file
            nama_dokumen = uploaded_file.name
            nomor, teks = nama_dokumen.split('_', 1)
            
            teks = teks.replace('.pdf', '')

            file_info = {"NRP": nomor,
                        "Nama siswa": teks,
                        "Tipe file": uploaded_file.type, 
                        "File size (bytes)": len(uploaded_file.read()),
                        "Info": "✅"}
            df_files_info = pd.concat([df_files_info, pd.DataFrame(file_info, index=[0])], ignore_index=True)


        if not df_files_info.empty:
            st.write("Informasi file yang diinput:")
            st.dataframe(df_files_info)
            st.write("Judul Database:")
            st.write(judul_database)


st.write("")

# PERHITUNGAN GATAU

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
#load_dotenv()
#genai.configure(api_key="AIzaSyDiEvJyv_j5ZLMDt6E6lSM3ytQTqvWEpUE")

# define function to generate content
def generate_gemini_content(tulisan, prompt):
    model=genai.GenerativeModel("gemini-pro")
    response=model.generate_content(prompt+tulisan)
    return response.text

# Prompt
prompt1="""You are a teacher correcting a student's document. You will be reading
        the answer text to a question and summarizing the key points within 250 words.
        Please provide a summary of the text given below:"""
prompt2='''You are a teacher correcting a student's document. You will read the text of an
answer to a question and summarise the key points in 250 words. Provide corrections
if there are words that are not correct, and provide criticism and suggestions.'''

# KODINGAN UNTUK BAGIAN BAWAH
pdf_data = {}  # Dictionary untuk menyimpan informasi dari setiap file PDF

try:
    if uploaded_files is not None:
        for uploaded_file in uploaded_files:
            if uploaded_file.type == "application/pdf":
                pdf_reader = PdfReader(uploaded_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                # Simpan informasi file PDF dalam dictionary dengan nama file sebagai kunci
                pdf_data[uploaded_file.name] = text
            elif uploaded_file.type == "application/zip":
                zip_file = zipfile.ZipFile(uploaded_file)
                for file_name in zip_file.namelist():
                    if file_name.endswith('.txt'):
                        with zip_file.open(file_name) as file:
                            text = file.read().decode("utf-8")
                            # Simpan informasi file dalam dictionary dengan nama file sebagai kunci
                            pdf_data[file_name] = text
except Exception as e:
    st.error(f"An error occurred: {e}")

pdf_df = pd.DataFrame.from_dict(pdf_data, orient='index', columns=['Text'])
if not pdf_df.empty:
    st.header("Text from PDFs:")
    st.dataframe(pdf_df)
    
# Confution matrix
kalimat = pdf_df['Text']
num_sentences = len(kalimat)
similarity_matrix = np.zeros((num_sentences, num_sentences))
embeddings = SentenceTransformer('all-MiniLM-L6-v2').encode(kalimat.tolist(), convert_to_tensor=True)

for i in range(num_sentences):
    for j in range(i + 1, num_sentences):
        similarity_matrix[i][j] = util.pytorch_cos_sim(embeddings[i], embeddings[j])
        
for i in range(num_sentences):
    for j in range(0, i):
        similarity_matrix[i][j] = similarity_matrix[j][i]
        
similarity_df = pd.DataFrame(similarity_matrix, columns=pdf_df.index, index=pdf_df.index)
sns.heatmap(similarity_df, mask=np.zeros_like(similarity_df),
            cmap=sns.diverging_palette(220, 10, as_cmap=True),
            square=True, annot=True)
st.pyplot(plt)