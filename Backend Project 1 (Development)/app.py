from flask import Flask, request, send_from_directory
import re

app = Flask(__name__)

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/match", methods=["POST"])
def match_regex():
    test_string = request.form.get("test_string")
    pattern = request.form.get("regex")

    try:
        matches = re.findall(pattern, test_string)
    except re.error as e:
        return f"<h3>Invalid Regular Expression</h3><p>{e}</p><a href='/'>Go Back</a>"

    result = "<h2>Matched Strings:</h2>"

    if matches:
        result += "<ul>"
        for m in matches:
            result += f"<li>{m}</li>"
        result += "</ul>"
    else:
        result += "<p>No matches found.</p>"

    result += "<br><a href='/'>Go Back</a>"
    return result

if __name__ == "__main__":
    app.run(debug=True)
