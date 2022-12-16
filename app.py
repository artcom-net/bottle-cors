import bottle

from bottlecors import CORSConfig, CORSPlugin

app = bottle.Bottle()

@app.get('/')
def get_route():
    # raise bottle.HTTPError(headers={'Vary': 'vasya'})
    # bottle.response.headers['Vary'] = 'Eduardo'
    # bottle.response.add_header('Vary', 'Eduardo')
    # bottle.response.add_header('Vary', 'Eduardo2')
    return {'method': 'GET'}


@app.route('/vasya', 'OPTIONS')
def options_route():
    # bottle.response.set_header('Vary', 'Eduardo')
    # bottle.response.headers['Vary'] = 'Eduardo'
    return {'method': 'OPTIONS'}


if __name__ == '__main__':
    cors_config = CORSConfig(allowed_credentials=True)
    app.install(CORSPlugin(cors_config))
    app.run()
