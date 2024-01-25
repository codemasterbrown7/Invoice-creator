from flask import Flask, render_template, request, session, redirect, url_for
import googlemaps
from datetime import datetime
from flask_session import Session
from openpyxl import Workbook
from flask import send_file
import pandas as pd 
import os
import tempfile


app = Flask(__name__)
app.secret_key = '7931'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

gmaps = googlemaps.Client(key='AIzaSyBOVpnUBMe217V09wm_f9cOzYpFYR-8sQY')

weekday_rate = 12
sat_rate = 13
sun_rate = 14
report_rate = 12
travel_time_rate = 11
mileage_rate = 0.30

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create-invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        num_families = int(request.form.get('num_families'))
        session['num_families'] = num_families
        # Initialize with family names as empty strings and empty meetings
        session['fws_tasks'] = {str(i): {'name': '', 'meetings': []} for i in range(1, num_families + 1)}
        session.modified = True
        return redirect(url_for('log_meetings'))
    return render_template('create_invoice.html')

@app.route('/log-meetings')
def log_meetings():
    num_families = session.get('num_families', 1)
    fws_tasks = session.get('fws_tasks', {})
    return render_template('log_meetings.html', num_families=num_families, fws_tasks=fws_tasks)

@app.route('/meeting-logger/<int:family_id>', methods=['GET', 'POST'])
def meeting_logger(family_id):
    family_id_str = str(family_id)
    if request.method == 'POST':
        selected_date = request.form.get('dateInput')
        def safe_float(value, default=0.0):
            try:
                return float(value) if value else default
            except ValueError:
                return default
            
        
        contact_hours = safe_float(request.form.get('supervisedContactHours', 0))
        report_hours = safe_float(request.form.get('contactReportHours', 0))
        travel_time_hours = safe_float(request.form.get('travelTimeHours', 0))
        admin_pre_confirmation = 'adminPreConfirmation' in request.form
        admin_new_case = 'adminNewCase' in request.form
        miscellaneous_cost = safe_float(request.form.get('miscellaneousCost', 0))
        addresses = request.form.getlist('addresses[]')
        family_name = request.form.get('family_name')

        family_name = request.form.get('family_name')
        if family_name:
            session['fws_tasks'][family_id_str]['name'] = family_name
            session.modified = True


        total_miles = 0
        for i in range(0, len(addresses)-1, 2):
            if addresses[i] and addresses[i+1]:
                distance_result = gmaps.directions(addresses[i], addresses[i+1], units="imperial")
                distance = distance_result[0]['legs'][0]['distance']['text']
                miles = float(distance.split()[0])
                total_miles += miles
        mileage_cost = total_miles * mileage_rate

        # Check if selected_date is not None before processing
        if selected_date:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
            if date_obj.weekday() == 5:
                contact_rate = sat_rate
            elif date_obj.weekday() == 6:
                contact_rate = sun_rate
            else:
                contact_rate = weekday_rate
        else:
            # Handle the case where no date is provided (use default rate or handle differently)
            contact_rate = weekday_rate
        
        admin_pre_confirmation_cost = 1 if admin_pre_confirmation else 0
        admin_new_case_cost = 2.75 if admin_new_case else 0

        contact_total = contact_hours * contact_rate
        report_total = report_hours * report_rate
        travel_time_total = travel_time_hours * travel_time_rate

        total = contact_total + report_total + travel_time_total + mileage_cost
        total += admin_pre_confirmation_cost + admin_new_case_cost
        total += miscellaneous_cost

        meeting_details = {
            'date': selected_date,
            'Supervised Contact Hours': {'value': contact_hours, 'rate': contact_rate, 'total': contact_total},
            'Contact Report Hours': {'value': report_hours, 'rate': report_rate, 'total': report_total},
            'Travel Time Hours': {'value': travel_time_hours, 'rate': travel_time_rate, 'total': travel_time_total},
            'Mileage': {'value': total_miles, 'rate': mileage_rate, 'total': mileage_cost},
            'Admin Pre Confirmation': {'value': admin_pre_confirmation, 'rate': 1, 'total': admin_pre_confirmation_cost},
            'Admin New Case': {'value': admin_new_case, 'rate': 2.75, 'total': admin_new_case_cost},
            'Miscellaneous': {'value': miscellaneous_cost, 'rate': 1, 'total': miscellaneous_cost}
        }



        session['fws_tasks'][family_id_str]['meetings'].append(meeting_details)
        session.modified = True
        return redirect(url_for('log_meetings'))

    # If GET request or no form data, just render the template
    family_name = session['fws_tasks'][family_id_str].get('name', '')
    return render_template('meeting_logger.html', family_id=family_id, family_name=family_name)

@app.route('/remove-meeting/<int:family_id>/<int:meeting_index>', methods=['POST'])
def remove_meeting(family_id, meeting_index):
    family_id_str = str(family_id)
    if family_id_str in session['fws_tasks']:
        meetings = session['fws_tasks'][family_id_str].get('meetings', [])
        if 0 <= meeting_index < len(meetings):
            # Remove the meeting at the specified index
            meetings.pop(meeting_index)
            session.modified = True
    return redirect(url_for('log_meetings'))


@app.route('/export-to-excel')
def export_to_excel():
    # Create a Pandas DataFrame from your session data
    data = []
    for family_id, family_info in session['fws_tasks'].items():
        for meeting in family_info['meetings']:
            row = {
                'Family Name': family_info['name'],
                'Meeting Date': meeting['date'],  # Assuming you store date in the meeting details
                'Task': None,  # Placeholder, will be populated in the loop below
                'Value': None,  # Placeholder
                'Rate': None,  # Placeholder
                'Total': None,  # Placeholder
            }
            for task, details in meeting.items():
                if task != 'date':  # Skip the date since it's already added
                    row.update({
                        'Task': task,
                        'Value': details['value'],
                        'Rate': details['rate'],
                        'Total': details['total']
                    })
                    data.append(row.copy())  # Append the updated row to the data list

    # Convert the data list to a DataFrame
    df = pd.DataFrame(data)

    grand_total = df['Total'].sum()

    # Append a row with the grand total at the end of the DataFrame
    grand_total_row = {'Task': 'Grand Total', 'Value': '', 'Rate': '', 'Total': grand_total}
    df = df.append(grand_total_row, ignore_index=True)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xlsx', delete=False) as tmp:
        # Write the dataframe to the temporary file
        with pd.ExcelWriter(tmp.name, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
            writer.save()
        
        tmp_path = tmp.name

    # Send the file for download
    return send_file(
        tmp_path,
        as_attachment=True,
        download_name='exported_data.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


if __name__ == '__main__':
    app.run(debug=True)
