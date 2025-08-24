from flask import Flask, render_template,request, jsonify
from utils.gcsp.helpers import load_questions, create_spending_chart
from utils.gcsp.Calculation import main_calc

app = Flask(__name__)

# -------------------------
# Home page with project list
# -------------------------
@app.route("/")
@app.route("/index")
def root():
    return render_template("home.html")   # contains links to GCSP + SBLE


# -------------------------
# GCSP App (SRI)
# -------------------------
@app.route("/srihome")
def srihome():
    questions = load_questions()
    return render_template("gcsp/sri_home.html", questions=questions)

@app.route("/sriresult", methods=["POST"])
def sriresult():
    form_data = request.get_json()  # AJAX sends JSON
    results = main_calc(form_data)
    print(results)
    # Extract numeric arrays for chart
    bm_arr = results['GCSP_result']['bm_spending_arr']
    mix_arr = results['GCSP_result']['mix_spending_arr']
    certainty_levels = [99, 95, 90, 80, 70, 60, 50, 40, 30, 20, 10, 5]  # must match array length
    
    # Generate chart
    chart_img = create_spending_chart(bm_arr, mix_arr, certainty_levels)

    # Render template
    rendered = render_template("gcsp/sri_result.html", results=results, chart_img=chart_img)
    return jsonify({"html": rendered})

# -------------------------
# SBLE App (placeholder for now)
# -------------------------
@app.route("/sblehome")
def sblehome():
    # You’ll create templates/sble_home.html later
    return render_template("sble_home.html")


