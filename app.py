from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "<h1>The Burrow Owls</h1><p>Book notes incoming…</p>"

if __name__ == "__main__":
    app.run()