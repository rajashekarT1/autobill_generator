import streamlit as st
import sqlite3 
from fpdf import FPDF
from datetime import datetime

conn = sqlite3.connect("auto_bill.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Clients(
               ID INTEGER PRIMARY KEY AUTOINCREMENT,
               Name TEXT NOT NULL,
               Contact_Details TEXT NOT NULL
               )
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Services(
               ID INTEGER PRIMARY KEY AUTOINCREMENT,
               Name TEXT NOT NULL,
               Rate REAL NOT NULL,
               Client_ID INTEGER NOT NULL,
               FOREIGN KEY(client_ID) REFERENCES Clients(ID)
                  
                )
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Invoices(
               ID INTEGER PRIMARY KEY AUTOINCREMENT,
               Client_ID INTEGER NOT NULL,
               tOTAL REAL NOT NULL,
               Date TEXT NOT NULL,
               FOREIGN KEY(client_ID) REFERENCES Clients(ID)
                  
                )
""")

conn.commit()

def generate_pdf(client,services,total,date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial",size=12)

    pdf.cell(200,10,txt="Invoice",ln=True,align="C")
    pdf.ln(10)

    pdf.cell(200,10,txt=f"Client:{client['Name']}",ln=True)
    pdf.cell(200,10,txt=f"Contact:{client['Contact_Details']}",ln=True)
    pdf.cell(200,10,txt=f"Date:{date}",ln=True)
    pdf.ln(10)

    pdf.cell(200,10,txt="Services",ln=True)
    for service in services:
        pdf.cell(200,10,txt=f"- {service['Name']}:${service['Rate']}",ln=True)
        pdf.ln(10)
        
    pdf.cell(200,10,txt=f"Total:${total}",ln=True)

    pdf_file = "invoice.pdf"
    pdf.output(pdf_file)
    return pdf_file

st.set_page_config(page_title="Auto Bill Generator",layout="wide")
st.markdown(
    """
<style>
body {
background-color:#233634;
color:white;
}
input,select,textarea {
color:black !important;
}
.stButton button{
background-color:#238923;
color:white;
}
.stSelectbox div {
color:black !important;
}
</style>

""",
unsafe_allow_html=True
)

st.title("Auto Bill Generator")
# st.markdown("""
# ### Welcome to the auto Bill Generator
# Easily manage clients,services,and invoices 
# """)

menu = ["Add Client","Add Service","Generate Invoice","View Invoices"]
choice = st.sidebar.selectbox("Menu",menu)

if choice == "Add Client":
    st.subheader("Add New Client")

    with st.form("add_client_form"):
        name = st.text_input("Client Name")
        contact = st.text_input("Contact Details")
        submitted = st.form_submit_button("Add Client")

        if submitted:
            if name and contact:
                if len(contact) == 10 and contact.isdigit():
                    cursor.execute("INSERT INTO Clients(Name,contact_Details)VALUES(?,?)",(name,contact))
                    conn.commit()
                    st.success("client added successfully")
                else:
                    st.error("contact details must be 10 digits")
            else:
                st.error("Please fill details")

elif choice == "Add Service":
    st.subheader("Add New Service")

    clients =cursor.execute("SELECT ID,Name FROM Clients").fetchall()
    client_dict = {client[1]:client[0] for client in clients}

    with st.form("add_service_form"):
        service_name = st.text_input("Service Name")
        service_rate = st.number_input("Rate",min_value=0.0,format="%.2f")
        client_name = st.selectbox("Select Client",list(client_dict.keys()))
        submitted = st.form_submit_button("Add Service")

        if submitted:
            if service_name and service_rate and client_name:
                cursor.execute(
                    "INSERT INTO Services(Name,Rate,Client_ID) VALUES(?,?,?)",
                    (service_name,service_rate,client_dict[client_name])
                )
                conn.commit()
                st.success("Service added successfully")
            else:
                st.error("please fill all details")
elif choice == "Generate Invoice":
    st.subheader("Generate Invoice")

    clients = cursor.execute("SELECT ID,Name FROM Clients").fetchall()
    client_dict = {client[1]:client[0] for client in clients}
    client_name = st.selectbox("Select Client",list(client_dict.keys()))
    if client_name:
        client_id = client_dict[client_name]
        services = cursor.execute("SELECT Name,Rate FROM Services WHERE Client_ID=?",(client_id,)).fetchall()
        total = sum(service[1] for service in services)

        st.markdown(f"### Services for {client_name}")
        for service in services:
          st.write(f"- {service[0]}: ${service[1]:.2f}")
          st.markdown(f"### Total:${total:.2f}")

        if st.button("Generate Invoice"):
            date = datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                "INSERT INTO Invoices (Client_ID,Total,Date) VALUES (?,?,?)",
                (client_id,total,date),
            )
            conn.commit()

            client = cursor.execute("SELECT Name, Contact_Details FROM Clients WHERE ID=?", (client_id,)).fetchone()
            client_data = {"Name": client[0], "Contact_Details": client[1]}

            service_data = [
                {
                    "Name":service[0],"Rate":service[1]
                }
                for service in services
            ]

            pdf_file = generate_pdf(client_data,service_data,total,date)
            with open(pdf_file,"rb") as file:
                st.download_button(
                    label="Download Invoice PDF",
                    data=file,
                    file_name=f"Invoice_{client_name}.pdf",
                    mime="application/pdf",
                )

elif choice == "View Invoices":
    st.subheader("View Invoices")

    invoices = cursor.execute("""
                SELECT Invoices.ID,Clients.Name,Invoices.Total,Invoices.Date
                FROM Invoices
                INNER JOIN Clients ON Invoices.Client_ID = Clients.ID
            """).fetchall()
    for invoice in invoices:
        st.markdown(f"### Invoice ID:{invoice[0]}")
        st.write(f"Client:{invoice[1]}")
        st.write(f"Total:${invoice[2]:.2f}")
        st.write(f"Date:{invoice[3]}")
        st.write("---")
    
    

