
from PIL import Image
import numpy as np
import pandas as pd
import easyocr
import regex as re
import streamlit as st
from streamlit_option_menu import option_menu
import base64
import sqlite3
import io
import cv2
import matplotlib.pyplot as plt
from tempfile import NamedTemporaryFile



# function to get text from image
def image_to_text(path):
  input_img= Image.open(path)

  #converting image to array format
  image_arr= np.array(input_img)

  reader= easyocr.Reader(['en'])
  text= reader.readtext(image_arr, detail= 0)

  return text, input_img

# function to get dict from impage text
def extracted_text(texts,input_img):

  extracted_dict = {"Name":[], "Designation":[], "Company name":[], "Contact":[], "Email":[], "Website":[],
                "Address":[], "Pincode":[], "Image":[]}

  extracted_dict["Name"].append(texts[0])
  extracted_dict["Designation"].append(texts[1])

  #Converting Image to Bytes
  Image_bytes = io.BytesIO()
  input_img.save(Image_bytes, format= "PNG")
  image_data = Image_bytes.getvalue()
  extracted_dict["Image"] = image_data

  for i in range(2,len(texts)):

    if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):

      extracted_dict["Contact"].append(texts[i])

    elif "@" in texts[i] and ".com" in texts[i]:
      extracted_dict["Email"].append(texts[i])

    elif "www" in texts[i].lower():
      small= texts[i].lower()
      extracted_dict["Website"].append(small)

    elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
      extracted_dict["Pincode"].append(texts[i])

    elif re.match(r'^[A-Za-z]', texts[i]):
      extracted_dict["Company name"].append(texts[i])

    else:
      remove_colon= re.sub(r'[,;]','',texts[i])
      extracted_dict["Address"].append(remove_colon)

  for key,value in extracted_dict.items():
    if key != 'Image':
      if len(value)>0:
        concadenate= " ".join(value)
        extracted_dict[key] = [concadenate]

      else:
        value = "NA"
        extracted_dict[key] = [value]

  return extracted_dict

def image_preview(image,res):
            for (bbox, text, prob) in res:
              # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15,15)
            plt.axis('off')
            plt.imshow(image)

#check if the table bizcard_details exist
def checkTable(cursor):
  q = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='bizcard_details'"
  cursor.execute(q)
  table1 = cursor.fetchall()
  names = []
  for i in table1:
      names.append(i[0])
  if (names[0] == 1):
    return True
  else:
    return False

#Function to display the sidebar background
def sidebar_bg(side_bg):

   side_bg_ext = 'png'

   st.markdown(
      f"""
      <style>
      [data-testid="stSidebar"] > div:first-child {{
          background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
      }}
      </style>
      """,


      unsafe_allow_html=True,
      )

side_bg = '/content/p1.png'
sidebar_bg(side_bg)

st.markdown("<h1 style='text-align: center; color: Green;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)


selected = option_menu(None, ["Home", "Save", "Edit", "Delete"],
                       icons=["house", "clipboard2-plus","eraser-fill", "clipboard2-minus"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "25px", "text-align": "centre", "margin": "-3px",
                                            "--hover-color": "#545454"},
                               "icon": {"font-size": "25px"},
                               "container": {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#ff5757"}})

# cursor for db connection
mydb = sqlite3.connect("bizcardx.db")
cursor = mydb.cursor()


# HOME MENU
if selected == "Home":
    col1, col2 = st.columns(2)

    st.write(
        "## :blue[**About :**] Bizcard is a Python application designed to extract information from business cards.")
    st.write(
        '## The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')

# DELETE MENU
if selected == "Delete":

  if (checkTable(cursor)):
      q = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='bizcard_details'"
      cursor.execute(q)

      col1,col2 = st.columns(2)
      with col1:

        select_query = "select name from bizcard_details"
        cursor.execute(select_query)
        table1 = cursor.fetchall()
        mydb.commit()
        names = []
        for i in table1:
          names.append(i[0])
        name_select = st.selectbox("Select the name", names)

      with col2:

        select_query = f"select designation from bizcard_details WHERE name ='{name_select}'"
        cursor.execute(select_query)
        table2 = cursor.fetchall()
        mydb.commit()
        designations = []
        for j in table2:
          designations.append(j[0])

        designation_select = st.selectbox("Select the designation", options = designations)

      if name_select and designation_select:
        col1,col2,col3 = st.columns(3)

        with col1:
          st.write(f"Selected Name : {name_select}")
          st.write(f"Selected Designation : {designation_select}")

        with col2:
          remove = st.button("Delete", use_container_width= True)

          if remove:
            cursor.execute(f"DELETE FROM bizcard_details WHERE NAME ='{name_select}' AND DESIGNATION = '{designation_select}'")
            mydb.commit()
            st.warning("DELETED",icon="⚠️")
  else:
    st.warning("No items in the table to delete",icon="⚠️")

# "Save"
if selected == "Save":
    image = st.file_uploader(label="Upload the image", type=['png', 'jpg', 'jpeg'], label_visibility="hidden")

    if image is not None:

      input_image = Image.open(image)

      col_1, col_2 = st.columns(2)
      if col_1:
        # Setting Image size
        st.image(input_image, caption='Uploaded Image')
      if col_2:
        st.set_option('deprecation.showPyplotGlobalUse', False)
        saved_img = image

        with NamedTemporaryFile(dir='.', suffix='.csv') as f:
          f.write(saved_img.getbuffer())
          img = cv2.imread(f.name)
          reader= easyocr.Reader(['en'])
          res = reader.readtext(img)
          st.pyplot(image_preview(img,res))

      text_image, input_img= image_to_text(image)
      text_dict = extracted_text(text_image,input_img)
      df= pd.DataFrame(text_dict)


      if text_dict:
        st.success("Extracted Sucessfully")
        df= pd.DataFrame(text_dict)
      else:
        st.error("Error while extracting")

      # Database

      col_1, col_2 = st.columns([4, 4])
      with col_1:
          modified_n = st.text_input('Name', text_dict["Name"][0])
          modified_d = st.text_input('Designation', text_dict["Designation"][0])
          modified_c = st.text_input('Company name', text_dict["Company name"][0])
          modified_con = st.text_input('Mobile', text_dict["Contact"][0])
          df["Name"], df["Designation"], df["Company name"], df[
              "Contact"] = modified_n, modified_d, modified_c, modified_con
      with col_2:
          modified_m = st.text_input('Email', text_dict["Email"][0])
          modified_w = st.text_input('Website', text_dict["Website"][0])
          modified_a = st.text_input('Address', text_dict["Address"][0][1])
          modified_p = st.text_input('Pincode', text_dict["Pincode"][0])
          df["Email"], df["Website"], df["Address"], df[
              "Pincode"] = modified_m, modified_w, modified_a, modified_p

      #col3, col4 = st.columns([4, 4])
      #with col3:
      Preview = st.button("Preview modified text")
      if Preview:
          filtered_df = df[
              ['Name', 'Designation', 'Company name', 'Contact', 'Email', 'Website', 'Address', 'Pincode','Image']]
          st.dataframe(filtered_df)
      else:
          pass
      #with col4:
      Upload = st.button("Upload")

      if Upload:
          with st.spinner("In progress"):
            mydb = sqlite3.connect("bizcardx.db")
            cursor = mydb.cursor()
            #Table Creation
            create_table_query = '''CREATE TABLE IF NOT EXISTS bizcard_details(name varchar(225),
                                                                                designation varchar(225),
                                                                                company_name varchar(225),
                                                                                contact varchar(225),
                                                                                email varchar(225),
                                                                                website text,
                                                                                address text,
                                                                                pincode varchar(225),
                                                                                image text)'''

            cursor.execute(create_table_query)
            mydb.commit()

            # Insert Query
            insert_query = '''INSERT INTO bizcard_details(name, designation, company_name,contact, email, website, address,
                                                          pincode, image)

                                                          values(?,?,?,?,?,?,?,?,?)'''

            filtered_df = df[
              ['Name', 'Designation', 'Company name', 'Contact', 'Email', 'Website', 'Address', 'Pincode','Image']]

            datas = filtered_df.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit()

            st.success("SAVED SUCCESSFULLY")

    else:
      st.write("Upload an image")

# "Edit"
if selected == "Edit":
  if (checkTable(cursor)):
      select_query = "select name from bizcard_details"
      cursor.execute(select_query)
      table1 = cursor.fetchall()
      mydb.commit()
      names = []
      for i in table1:
        names.append(i[0])
      name_select = st.selectbox("Select the card to edit", names)

      select_query1 = f"select * from bizcard_details WHERE name ='{name_select}'"
      cursor.execute(select_query1)
      table2 = cursor.fetchall()
      mydb.commit()
      names = []
      df = pd.DataFrame()
      for i in table2:
          names.append(i)

      # Database
      if( names ):
        col_1, col_2 = st.columns([4, 4])
        with col_1:
          modified_n = st.text_input('Name', names[0][0])
          modified_d = st.text_input('Designation', names[0][1])
          modified_c = st.text_input('Company name', names[0][2])
          modified_con = st.text_input('Mobile', names[0][3])
          df["Name"], df["Designation"], df["Company name"], df[
              "Contact"] = modified_n, modified_d, modified_c, modified_con
        with col_2:
          modified_m = st.text_input('Email', names[0][4])
          modified_w = st.text_input('Website', names[0][5])
          modified_a = st.text_input('Address', names[0][6])
          modified_p = st.text_input('Pincode', names[0][7])
          df["Email"], df["Website"], df["Address"], df[
              "Pincode"] = modified_m, modified_w, modified_a, modified_p

        
        df['Image'] = names[0][7]
        #col3, col4 = st.columns([4, 4])
        #with col3:
        Preview = st.button("Preview Edited text")
        if Preview:
          filtered_df = df[
              ['Name', 'Designation', 'Company name', 'Contact', 'Email', 'Website', 'Address', 'Pincode','Image']]
          st.dataframe(filtered_df)
        else:
          pass
        #with col4:
        Upload = st.button("Edit")

        if Upload:
          with st.spinner("In progress"):
            mydb = sqlite3.connect("bizcardx.db")
            cursor = mydb.cursor()
            cursor.execute(f"DELETE FROM bizcard_details WHERE NAME ='{name_select}'")
            mydb.commit()

            # Insert Query
            insert_query = '''INSERT INTO bizcard_details(name, designation, company_name,contact, email, website, address,
                                                          pincode, image)

                                                          values(?,?,?,?,?,?,?,?,?)'''

            filtered_df = df[
              ['Name', 'Designation', 'Company name', 'Contact', 'Email', 'Website', 'Address', 'Pincode','Image']]

            datas = filtered_df.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit()

            st.success("EDITED DETAILS SAVED SUCCESSFULLY")

  else:
    st.warning("No items in the table to edit",icon="⚠️")











