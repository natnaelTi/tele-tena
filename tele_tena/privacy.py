"""Keep authenticated app responses out of browser and intermediary caches."""
def no_store(response, request):
    if request.path.startswith('/api/method/tele_tena.'):
        response.headers['Cache-Control'] = 'no-store, private'
        response.headers['Pragma'] = 'no-cache'
