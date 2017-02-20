import web
import ConfigurationELSA as elsa
import hashlib
import binascii
import time


render=web.template.render('templates/',base='layout')

urls = (
    '/', 'WebIndex',
    '/index','WebIndex',
    '/place/(.+)', 'WebPlace',
    '/places', 'WebPlaces',
    '/equipments', 'WebEquipments',
    '/equipment/(.+)','WebEquipment',
)
#Configuration Singleton ELSA
c=elsa.Configuration()
c.load()

#print c.AllLanguages.elements['FR'].fields['welcome']

class WebObject():
    def __init__(self):
	self.name = u"WebIndex"
    def GET(self):
	mail = isConnected()
	if mail is not None:
	    if self.name == u"WebPlaces":
		return render.places(c,mail)
	    elif self.name == u"WebEquipments":
		return render.equipments(c,mail)
	    else:
		return render.index(True, c, mail)
	return render.index(False,c,'')
	
class WebObjectUpdate():
    def GET(self,id):
	mail = isConnected()
	if mail is not None:
	    if self.name == u"WebPlace":
		return render.place(c,id,mail)
	    elif self.name == u"WebEquipment":
		return render.equipment(c,id,mail)
	raise web.seeother('/')
	
    def POST(self, id):
	mail = isConnected()
	if mail is not None:
	    currObject = c.getObject(id,self.name)
	    if currObject is None:
		raise web.seeother('/')
	    data = web.input(nifile={})
	    method = data.get("method","malformed")
	    for key in c.getFieldsname(self.name):
		if key in data:
		    currObject[key] = data[key]
	    try:
		currObject['deny'] = data.deny
	    except:
		currObject['deny'] = 0
	    currObject.save(c,c.connectedUsers.users[mail].cuser)
	    return render.places(c,mail)
	raise web.seeother('/')
	
class WebIndex(WebObject):
    def __init(self):
	self.name = u"WebIndex"
	
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
	
class WebPlaces(WebObject):
    def __init__(self):
	self.name=u"WebPlaces"
	
class WebEquipments(WebObject):
    def __init__(self):
	self.name=u"WebEquipments"


class WebPlace(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebPlace"

	
class WebEquipment(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebEquipment"
	

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

def printInfo( info):
    print info.items()
    print '\n'

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
