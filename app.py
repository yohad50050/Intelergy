import requests
from flask import Flask, request, render_template

app = Flask(__name__)
BASE_URL = "http://192.168.1.161"


@app.route("/", methods=["GET", "POST"])
def get_plug_info():
    voltage = "Unavailable"
    power = "Unavailable"
    switch_state = "Unavailable"
    temperature = "Unavailable"
    message = None

    if request.method == "GET":
        try:
            response = requests.get(f"{BASE_URL}/rpc/Shelly.GetStatus", timeout=5)
            if response.status_code == 200:
                plug_data = response.json()
                voltage = plug_data.get("switch:0", {}).get("voltage", "OFF")
                power = plug_data.get("switch:0", {}).get("apower", "Unavailable")
                switch_state = (
                    "ON"
                    if plug_data.get("switch:0", {}).get("output", False)
                    else "OFF"
                )
                temperature = (
                    plug_data.get("switch:0", {})
                    .get("temperature", {})
                    .get("tC", "Unavailable")
                )
            else:
                message = f"Failed to retrieve data: {response.status_code}"
        except requests.exceptions.RequestException as err:
            message = f"Error fetching data: {err}"

    elif request.method == "POST":
        action = request.form.get("action")
        if action not in ["on", "off"]:
            return "Invalid action. Use 'on' or 'off'.", 400

        try:
            response = requests.post(
                f"{BASE_URL}/rpc/Switch.Set",
                json={"id": 0, "on": (action == "on")},
                timeout=5,
            )
            if response.status_code == 200:
                switch_state = "ON" if action == "on" else "OFF"
                message = f"Plug turned {action} successfully!"
            else:
                message = (
                    f"Failed to turn plug {action}. Status: {response.status_code}"
                )
        except requests.exceptions.RequestException as err:
            message = f"Error toggling plug: {err}"

    return render_template(
        "first_web.html",
        voltage=voltage,
        power=power,
        switch=switch_state,
        temperature=temperature,
        message=message,
    )


if __name__ == "__main__":
    app.run(debug=True)
