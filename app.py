from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "Burrow Owls is live 🦉📚"

if __name__ == "__main__":
    app.run()