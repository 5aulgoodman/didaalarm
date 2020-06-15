from didaalarm import app,app
from .upload import upload
from .queryhouse import queryhouse
app.register_blueprint(upload,url_prefix='/upload')
app.register_blueprint(queryhouse,url_prefix='/queryhouse')
# app.register_blueprint(queryhouse,url_prefix='/bocshift')