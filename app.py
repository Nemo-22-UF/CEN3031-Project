from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Skill-It is running"

if __name__ == "__main__":
    app.run(debug=True)