"""Keep authenticated app responses out of browser and intermediary caches."""
def no_store(response, request):
    from tele_tena.review import enabled
    if (request.path.startswith('/api/method/tele_tena.') or
            (enabled() and request.path.startswith(('/api/', '/private/')))):
        response.headers['Cache-Control'] = 'no-store, private'
        response.headers['Pragma'] = 'no-cache'
