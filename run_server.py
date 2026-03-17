try:
    from app import create_app
    print('App imported', flush=True)
    app = create_app()
    print('App created', flush=True)
    app.run(host='0.0.0.0', port=5050, debug=False, use_reloader=False)
except Exception as e:
    print(f'Error: {e}', flush=True)
    import traceback
    traceback.print_exc()
