from app import create_app

app = create_app()

if __name__ == '__main__':
    # Lance le serveur web
    app.run(debug=True)