# app.py
# Phase 7: the web version of the maintenance delay tracker.
# Run it with:  python app.py
# Then open http://127.0.0.1:5000 in your browser.

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    """The home page."""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)