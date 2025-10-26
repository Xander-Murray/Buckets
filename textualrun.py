def main():
    from Buckets.config import load_config

    load_config()

    from Buckets.models.database.app import init_db

    init_db()

    from Buckets.app import App

    app = App()
    app.run()


if __name__ == "__main__":
    main()
