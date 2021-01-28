from Simulation import create_app

app = create_app()

if __name__ == '__main__':
    # use_reloader=False prevents create_app from being called twice
    app.run(debug=True, use_reloader=False)
