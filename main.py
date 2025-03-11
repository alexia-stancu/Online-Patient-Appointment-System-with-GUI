import tkinter as tk
from tkinter import messagebox
import sqlite3

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

global appointments_window
appointments_window = None


#Crearea bazei de date si a tabelului daca nu exista
def create_db():
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            phone_number TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def initialize_count_db():
    conn = sqlite3.connect('run_counter_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS run_count (id INTEGER PRIMARY KEY, count INTEGER)")
    cursor.execute("INSERT OR IGNORE INTO run_count (id, count) VALUES (1, -1)")
    conn.commit()
    conn.close()

initialize_count_db()

def get_and_increment_count():
    conn = sqlite3.connect('run_counter_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM run_count WHERE id = 1")
    count = cursor.fetchone()[0]
    count += 1
    count %= 7
    cursor.execute("UPDATE run_count SET count = ? WHERE id = 1", (count,))
    conn.commit()
    conn.close()
    return count

def create_doctors_db():
    conn = sqlite3.connect('doctors_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            phone_number TEXT NOT NULL
        )
    ''')
    #Verificam daca tabelul este gol
    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]
    if count == 0:
        #Tabelul este gol, adaugam doctorii
        doctors = [
            ("Dr. Popescu", "Cardiologie", "drpop@gmail.com"),
            ("Dr. Ionescu", "Neurologie", "drionescu@yahoo.com"),
            ("Dr. Vasilescu", "Ortopedie", "drvasi@icloud.com")
        ]
        cursor.executemany("INSERT INTO doctors (name, specialty, phone_number) VALUES (?, ?, ?)", doctors)

    conn.commit()
    conn.close()

#Apelam functia pentru a crea baza de date a doctorilor
create_doctors_db()

def create_schedule_db():
    conn = sqlite3.connect('doctors_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            doctor_id INTEGER,
            day TEXT NOT NULL,
            hour TEXT NOT NULL,
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    ''')

    #Verificam numarul de doctori pentru a nu duplica orarele
    cursor.execute("SELECT COUNT(*) FROM doctors")
    doctor_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM schedules")
    schedule_count = cursor.fetchone()[0]

    if doctor_count > 0 and schedule_count == 0:
        days = ["Luni", "Marți", "Miercuri", "Joi", "Vineri"]
        hours = ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
        cursor.execute("SELECT id FROM doctors")
        doctor_ids = [id[0] for id in cursor.fetchall()]

        for doctor_id in doctor_ids:
            for day in days:
                for hour in hours:
                    cursor.execute("INSERT INTO schedules (doctor_id, day, hour) VALUES (?, ?, ?)", (doctor_id, day, hour))

    conn.commit()
    conn.close()

create_schedule_db()

def create_appointments_db():
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            doctor_id INTEGER,
            date TEXT,
            time TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    ''')
    conn.commit()
    conn.close()

create_appointments_db()

def make_appointment(doctor_id, date, time, patient_id, schedule_window):
    #Adaugarea programarii în baza de date
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (patient_id, doctor_id, date, time) VALUES (?, ?, ?, ?)", (patient_id, doctor_id, date, time))
    conn.commit()
    conn.close()
    

    conn_doctor = sqlite3.connect('doctors_db.sqlite')
    cursor_doctor = conn_doctor.cursor()
    #Stergem programarea din baza de date a doctorului
    cursor_doctor.execute("DELETE FROM schedules WHERE doctor_id = ? AND day = ? AND hour = ?", (doctor_id, date, time))
    conn_doctor.commit()
    conn_doctor.close()
    schedule_window.destroy()
    #show_schedule(doctor_id)
    messagebox.showinfo("Succes", "Programare realizată cu succes!")

    #Extrage adresa de email a pacientului din baza de date
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number FROM patients WHERE id = ?", (patient_id,))
    email = cursor.fetchone()[0]
    conn.close()

    #Extrage numele pacientului din baza de date
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM patients WHERE id = ?", (patient_id,))
    patient_name = cursor.fetchone()[0]
    conn.close()

    #Extrage numele doctorului din baza de date
    conn = sqlite3.connect('doctors_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM doctors WHERE id = ?", (doctor_id,))
    doctor_name = cursor.fetchone()[0]
    conn.close()

    #Trimite emailul de confirmare a programarii
    email_subject = "Confirmare Programare"
    email_body = f"Draga {patient_name}, va confirmam programarea cu {doctor_name} pentru ziua de {date}, la ora {time}. Va asteptam cu drag!"
    send_email(email, email_subject, email_body)
    

def send_email(to_email, subject, body):
    #Configureaza serverul de email si informatiile de autentificare ale expeditorului
    sender_email = "alexia.stancu@yahoo.com"
    sender_password = "ParolaDeNedescifrat18;"

    #Creeaza email-ul
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    #Defineste continutul textului email-ului si il adauga ca un atasament la mesajul care va fi trimis
    message.attach(MIMEText(body, "plain"))

    print(sender_email,"\n", to_email, "\n", message, "\n")

    #Conectarea la server si trimiterea email-ului
    server = smtplib.SMTP("smtp.mail.yahoo.com", 587)
    status_code, response = server.ehlo()
    print(f"[*] Echoing the server: {status_code} {response}")
    status_code, response = server.starttls()
    print(f"[*] Starting TLS connection: {status_code} {response}")
    status_code, response = server.login(sender_email, sender_password)
    print(f"[*] Logging in: {status_code} {response}")

    server.sendmail(sender_email, to_email, message.as_string())
    server.quit()

def on_canvas_configure(canvas, event):
    #Seteaza regiunea de defilare pentru a include tot continutul canvas-ului
    canvas.configure(scrollregion=canvas.bbox("all"))

def show_schedule(doctor_id):
    schedule_window = tk.Toplevel(root)
    schedule_window.title("Orar Doctor")
    schedule_window.state('zoomed')

    conn = sqlite3.connect('doctors_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT day, hour FROM schedules WHERE doctor_id = ?", (doctor_id,))
    schedule = cursor.fetchall()

    #Creeaza un canvas si o bara de scroll verticala
    canvas = tk.Canvas(schedule_window)
    vsb = tk.Scrollbar(schedule_window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    #Creeaza un frame in interiorul canvas-ului
    inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    canvas.bind("<Configure>", lambda event, canvas=canvas: on_canvas_configure(canvas, event))

    for i, slot in enumerate(schedule):
        tk.Label(inner_frame, text=f"{slot[0]}: {slot[1]}").grid(row=i, column=0)
        tk.Button(inner_frame, text="Programare", command=lambda d=doctor_id, dt=slot[0], tm=slot[1]: make_appointment(d, dt, tm, current_patient_id, schedule_window)).grid(row=i, column=1)
    
    conn.close()

def view_appointments(patient_id):
    global appointments_window
    appointments_window = tk.Toplevel(root)
    appointments_window.title("Programările Mele")
    appointments_window.state('zoomed')

    #Conexiunea la baza de date a pacientilor
    conn_patient = sqlite3.connect('patient_db.sqlite')
    cursor_patient = conn_patient.cursor()

    #Conexiunea la baza de date a doctorilor
    conn_doctor = sqlite3.connect('doctors_db.sqlite')
    cursor_doctor = conn_doctor.cursor()

    cursor_patient.execute("SELECT id, doctor_id, date, time FROM appointments WHERE patient_id = ?", (patient_id,))
    appointments = cursor_patient.fetchall()

    center_frame = tk.Frame(appointments_window)
    center_frame.pack(expand=True)

    tk.Label(center_frame, text="Data").grid(row=0, column=0)
    tk.Label(center_frame, text="Ora").grid(row=0, column=1)
    tk.Label(center_frame, text="Doctor").grid(row=0, column=2)
    tk.Label(center_frame, text="Specialitate").grid(row=0, column=3)

    for i, appointment in enumerate(appointments):
        doctor_id = appointment[1]
        cursor_doctor.execute("SELECT name, specialty FROM doctors WHERE id = ?", (doctor_id,))
        doctor_info = cursor_doctor.fetchone()
        
        tk.Label(center_frame, text=appointment[2]).grid(row=i+1, column=0)  #Data
        tk.Label(center_frame, text=appointment[3]).grid(row=i+1, column=1)  #Ora
        tk.Label(center_frame, text=doctor_info[0]).grid(row=i+1, column=2)  #Numele doctorului
        tk.Label(center_frame, text=doctor_info[1]).grid(row=i+1, column=3)  #Specialitatea doctorului

        appointment_id = appointment[0]  #id-ul programarii
        doctor_id = appointment[1]  #id-ul doctorului
        date = appointment[2]  #Data programarii
        time = appointment[3]  #Ora programarii
        #print("doc_id = ", doctor_id)

        tk.Button(center_frame, text="Eliminare", command=lambda a_id=appointment_id, d_id=doctor_id, dt=date, tm=time: delete_appointment(a_id, d_id, dt, tm)).grid(row=i+1, column=4)

    def back_to_menu():
        global appointments_window
        appointments_window.destroy()
        appointments_window = None

    #Buton return menu
    menu = tk.Button(center_frame, text = "Menu", command = back_to_menu)
    menu.grid(row = len(appointments)+2, column = 0, columnspan = 4)

    conn_patient.close()
    conn_doctor.close()

def delete_appointment(appointment_id, doctor_id, date, time):
    global appointments_window
    #Stergerea programarii din baza de date a pacientilor
    conn_patient = sqlite3.connect('patient_db.sqlite')
    cursor_patient = conn_patient.cursor()
    cursor_patient.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn_patient.commit()
    conn_patient.close()

    #Adaugarea intervalului orar inapoi în baza de date a doctorilor
    conn_doctor = sqlite3.connect('doctors_db.sqlite')
    cursor_doctor = conn_doctor.cursor()
    cursor_doctor.execute("INSERT INTO schedules (doctor_id, day, hour) VALUES (?, ?, ?)", (doctor_id, date, time))
    conn_doctor.commit()
    conn_doctor.close()

    appointments_window.destroy()
    messagebox.showinfo("Succes", "Programarea a fost eliminată cu succes!")
    #Reimprospatarea ferestrei cu programarile
    view_appointments(current_patient_id)

def open_doctor_selection():
    doctor_window = tk.Toplevel(root)
    doctor_window.title("Menu")
    doctor_window.state('zoomed')

    conn = sqlite3.connect('doctors_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, specialty, phone_number FROM doctors")
    doctors = cursor.fetchall()

    center_frame = tk.Frame(doctor_window)
    center_frame.pack(expand=True)

    tk.Label(center_frame, text="Nume").grid(row=0, column=0)
    tk.Label(center_frame, text="Specialitate").grid(row=0, column=1)
    tk.Label(center_frame, text="Adresa Email").grid(row=0, column=2)

    for i, doctor in enumerate(doctors):
        tk.Label(center_frame, text=doctor[1]).grid(row=i+1, column=0)
        tk.Label(center_frame, text=doctor[2]).grid(row=i+1, column=1)
        tk.Label(center_frame, text=doctor[3]).grid(row=i+1, column=2)
        #Adaugam butonul de "Programare"
        tk.Button(center_frame, text="Programare", command=lambda d=doctor[0]: show_schedule(d)).grid(row=i+1, column=3)
    
    #Buton pentru vizualizarea programarilor
    global appointments_window
    view_appointments_button = tk.Button(
        center_frame, 
        text="Vizualizare Programări", 
        command=lambda: view_appointments(current_patient_id) if appointments_window is None else None
    )    
    view_appointments_button.grid(row=len(doctors) + 1, column=0, columnspan=2)
    conn.close()

    def on_close():
        root.deiconify()  #Reafisează fereastra principala
        root.state('zoomed')
        doctor_window.destroy()  #Inchide fereastra "Menu"

    #Legatura intre evenimentul de închidere si funcția on_close
    doctor_window.protocol("WM_DELETE_WINDOW", on_close)    

def open_register_window():
    register_window = tk.Toplevel(root)
    register_window.title("Creare Cont Nou")
    register_window.state('zoomed')

    #Crearea unui frame pentru centrarea elementelor
    center_frame = tk.Frame(register_window)
    center_frame.pack(expand=True)

    #Crearea campurilor de formular pentru inregistrare
    tk.Label(center_frame, text="Nume").pack()
    register_name_entry = tk.Entry(center_frame)
    register_name_entry.pack()

    tk.Label(center_frame, text="Adresa Email").pack()
    register_phone_entry = tk.Entry(center_frame)
    register_phone_entry.pack()

    tk.Label(center_frame, text="Parola").pack()
    register_password_entry = tk.Entry(center_frame, show="*")
    register_password_entry.pack()

    #Buton pentru crearea contului nou
    register_button = tk.Button(center_frame, text="Creare Cont", command=lambda: register_patient(register_name_entry.get(), register_phone_entry.get(), register_password_entry.get(), register_window))
    register_button.pack()

    #Centrarea frame-ului
    center_frame.pack(expand=True)


def login(username, password):
    global current_patient_id
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM patients WHERE name = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result and result[1] == password:
        current_patient_id = result[0]  #Salvam id-ul pacientului
        root.withdraw()
        open_doctor_selection()
    else:
        messagebox.showinfo("Eroare", "Numele de utilizator sau parola incorectă!")

def register_patient(name, phone, password, window):
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO patients (name, password, phone_number) VALUES (?, ?, ?)", (name, password, phone))
    conn.commit()
    conn.close()
    messagebox.showinfo("Succes", "Cont creat cu succes!")
    window.destroy()
    #open_doctor_selection()

#Initializarea bazei de date
create_db()

def find_appointments_on_date(ziua):
    #Conectarea la baza de date
    conn = sqlite3.connect('patient_db.sqlite')
    cursor = conn.cursor()

    #Executarea interogarii SQL pentru a gasi programarile din ziua specificata
    cursor.execute("SELECT patient_id, time FROM appointments WHERE date = ?", (ziua,))
    appointments = cursor.fetchall()
    print(appointments)
    for appointment in appointments:
        patient_id = appointment[0]
        cursor.execute("SELECT phone_number, name FROM patients WHERE id = ?", (patient_id,))
        email, patient_name = cursor.fetchone()
        email_subject = "Kind Reminder"
        email_body = f"Draga {patient_name}, va reamintim ca aveti programare pentru ziua de {ziua}, la ora {appointment[1]}. Va asteptam cu drag!"
        send_email(email, email_subject, email_body)

    conn.close()

root = tk.Tk()
root.title("Sistem de Programare Online pentru Pacienți")
root.state('zoomed')

#Crearea unui cadru pentru centrarea elementelor
form_frame = tk.Frame(root)
form_frame.pack(expand=True)

#Crearea campurilor de formular în cadrul creat
tk.Label(form_frame, text="Nume").grid(row=0, column=0)
name_entry = tk.Entry(form_frame)
name_entry.grid(row=0, column=1)

tk.Label(form_frame, text="Parola").grid(row=1, column=0)
password_entry = tk.Entry(form_frame, show="*")
password_entry.grid(row=1, column=1)

#Buton pentru conectare
login_button = tk.Button(form_frame, text="Conectare", command=lambda: login(name_entry.get(), password_entry.get()))
login_button.grid(row=2, column=0, columnspan=2)

#Buton pentru crearea unui nou cont
register_button = tk.Button(form_frame, text="Creare Cont", command=open_register_window)
register_button.grid(row=3, column=0, columnspan=2)

root.mainloop()

zile_saptamana = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
ziua = zile_saptamana[get_and_increment_count()]
print(ziua)
find_appointments_on_date(ziua)

