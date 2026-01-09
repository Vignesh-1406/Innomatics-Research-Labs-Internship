from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def home():
    name = request.args.get("name")

    if name:
        upper_name = name.upper()
        reversed_name = name[::-1].lower()
        name_length = len(name)

        return render_template(
            "index.html",
            name=name,
            upper_name=upper_name,
            reversed_name=reversed_name,
            name_length=name_length
        )

    return "<h2>Provide the name in the URL, like:  <code>127.0.0.1:5000?name=Vignesh</code></h2>"

if __name__ == "__main__":
    app.run(debug=True)
