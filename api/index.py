from app import app
from vercel_wsgi import make_handler

handler = make_handler(app)
