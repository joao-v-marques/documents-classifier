from routes.render_pages.render_home import bp_render_home

PREFIX = "/classificador-documentos"

def config_all(app):
    config_bps(app)

def config_bps(app):
    app.register_blueprint(bp_render_home, url_prefix=PREFIX)