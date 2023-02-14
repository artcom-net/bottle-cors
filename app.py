import bottle

from bottlecors import CORSConfig, CORSPlugin

app = bottle.Bottle()


# @app.hook('before_request')
# def handle_options():
#     print('')
#
#
@app.hook('after_request')
def enable_cors():
    bottle.response.set_header('Vary', 'Eduardo')

@app.error(405)
def handle_405(error):
    return 'Vasya405'

@app.error(404)
def handle_405(error):
    return 'Vasya404'


@app.get('/')
def get_route():
    # raise bottle.HTTPError(headers={'Vary': 'vasya'})
    # bottle.response.headers['Vary'] = 'Eduardo'
    # bottle.response.add_header('Vary', 'Eduardo')
    # bottle.response.add_header('Vary', 'Eduardo2')
    raise bottle.HTTPError()
    # return {'method': 'GET'}


@app.route('/vasya', 'OPTIONS')
def options_route():
    # bottle.response.set_header('Vary', 'Eduardo')
    # bottle.response.headers['Vary'] = 'Eduardo'
    return {'method': 'OPTIONS'}


if __name__ == '__main__':
    cors_config = CORSConfig(allowed_credentials=True, exposed_headers=['Content-Type',])
    app.install(CORSPlugin(cors_config))
    app.run()
