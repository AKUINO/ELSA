import web
import ConfigurationELSA as elsa
import hashlib
import binascii
import time


render=web.template.render('templates/',base='layout')

urls = (
    '/', 'Index',
    '/index','Index',
    '/place/(.+)', 'Place',
    '/places', 'Places',
)
#Configuration Singleton ELSA
c=elsa.Configuration()
c.load()

print c.AllLanguages.elements['francais']

class Index:
    def GET(self):
	mail = isConnected()
	if mail is not None:
	    return render.index(True, c, mail)
        return render.index(False, c, '')
    def POST(self):
	data = web.input(nifile={})
	method = data.get("method","malformed")
	connectedUser = connexion(data._username_,data._password_)
	if connectedUser is not None:
	    infoCookie = data._username_ + ',' + connectedUser.fields['password']
	    web.setcookie('webpy', infoCookie, expires=900)
	    c.connectedUsers.addUser(connectedUser)
	    return render.index(True, c, data._username_) 
	return render.index(False, c, '')
class Places:
    def GET(self):
	mail = isConnected()
	if mail is not None :
	    return render.places(c,mail)
	raise web.seeother('/')

class Place:
    def GET(self,id):
	if ifConnected() is not None:
	    return render.place(c.AllPieces.elements[str(id)].fields)
	return render.index(False, c, '')

def encrypt(password,salt):
    sha = hashlib.pbkdf2_hmac('sha256', password, salt, 126425)
    return binascii.hexlify(sha)

def connexion(username,password):
    user = c.AllUsers.getUser(username)
    if user is not None:
	cryptedPassword = encrypt(password,user.fields['registration'])
	if user.checkPassword(cryptedPassword) is True:
	    return user
    return None
    
def isConnected():
    infoCookie = web.cookies().get('webpy')
    if infoCookie is not None : 
	infoCookie = infoCookie.split(',')
	if c.connectedUsers.isConnected(infoCookie[0],infoCookie[1]) is True:
	    return infoCookie[0]
    return None

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
