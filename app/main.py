from flask import Flask, jsonify, request, render_template
from database import get_connection


app = Flask(__name__)


# ---------------- HOME ----------------
@app.route("/")
def home():
    return jsonify({"message": "Smart Appointment System is running"})


# ---------------- CREATE USER ----------------
@app.route("/users", methods=["POST"])
def create_user():

    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")

    if not name or not email or not phone:
        return "All fields are required", 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)",
        (name, email, phone)
    )

    conn.commit()

    user_id = cursor.lastrowid  # ⭐ AUTO GENERATED USER ID

    cursor.close()
    conn.close()

    return render_template(
        "user_created.html",
        user_id=user_id
    )




# ---------------- BOOK APPOINTMENT ----------------

@app.route("/appointments", methods=["POST"])
def book_appointment():

    # 👉 FORM se data lo
    user_id = request.form.get("user_id")
    appointment_date = request.form.get("appointment_date")
    appointment_time = request.form.get("appointment_time")

    if not user_id or not appointment_date or not appointment_time:
        return "All fields are required", 400

    conn = get_connection()
    cursor = conn.cursor()

    # Count appointments for same date
    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE appointment_date = %s",
        (appointment_date,)
    )
    count = cursor.fetchone()[0]

    queue_number = count + 1

    cursor.execute(
        """
        INSERT INTO appointments
        (user_id, appointment_date, appointment_time, queue_number, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, appointment_date, appointment_time, queue_number, "BOOKED")
    )

    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
    "success.html",
    message="Appointment Booked Successfully",
    queue=queue_number
)




# ---------------- GET ALL APPOINTMENTS ----------------
@app.route("/appointments", methods=["GET"])
def get_appointments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            appointments.id,
            users.name,
            users.email,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.queue_number,
            appointments.status
        FROM appointments
        JOIN users ON appointments.user_id = users.id
        ORDER BY appointments.appointment_date, appointments.queue_number
    """)

    appointments = cursor.fetchall()

    # FIX: Convert date & time to string (JSON safe)
    for appt in appointments:
        appt["appointment_date"] = str(appt["appointment_date"])
        appt["appointment_time"] = str(appt["appointment_time"])

    cursor.close()
    conn.close()

    return jsonify(appointments)
# html
@app.route("/register")
def register_page():
    return render_template("user.html")


@app.route("/ui")
def ui():
    return render_template("user.html")

@app.route("/admin")
def admin():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT users.name, appointments.appointment_date,
               appointments.appointment_time,
               appointments.queue_number, appointments.status
        FROM appointments
        JOIN users ON appointments.user_id = users.id
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin.html", appointments=data)


    



# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
