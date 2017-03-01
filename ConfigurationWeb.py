import web
import ConfigurationELSA as elsa
import hashlib
import binascii
import time


render=web.template.render('templates/',base='layout')

urls = (
    '/', 'WebIndex',
    '/index','WebIndex',
    '/places/(.+)', 'WebPlace',
    '/places/', 'WebPlaces',
    '/equipments', 'WebEquipments',
    '/equipments/(.+)','WebEquipment',
    '/users/', 'WebUsers',
    '/users/(.+)', 'WebUser',
    '/groups/', 'WebGroups',
    '/groups/(.+)', 'WebGroup',
    '/permissions/(.+)', 'WebPermission',
)
#Configuration Singleton ELSA
c=elsa.Configuration()
c.load()


class WebObject():
    def __init__(self):
	self.name = u"WebIndex"
    def GET(self):
	mail = isConnected()
	if mail is not None:
	    return self.getRender(mail)
	return render.index(False,c,'')
	
class WebObjectUpdate():
    def GET(self,id):
	mail = isConnected()
	if mail is not None:
	    return self.getRender(id,mail)
	raise web.seeother('/')
	
    def POST(self, id):
	mail = isConnected()
	user  = c.connectedUsers.users[mail].cuser
	if mail is not None:
	    currObject = c.getObject(id,self.name)
	    imgDirectory = 'static/img'
	    
	    if currObject is None:
		raise web.seeother('/')
		
	    data = web.input(placeImg={})
	    method = data.get("method","malformed")
	    for key in c.getFieldsname(self.name):
		if key in data:
		    currObject.fields[key] = data[key]
		    
	    for key in c.AllLanguages.elements:
		if key in data:
		    currObject.setName(key, data[key],user, c.getKeyColumn(currObject))
		    
	    if 'deny'in data:
		currObject.fields['deny'] = 1
	    else:
		currObject.fields['deny'] = 0
		
	    if currObject.creator is None:
		currObject.creator = user.fields['u_id']
		currObject.created = currObject.fields['begin']
		
	    if 'password' in currObject.fields:
		currObject.fields['registration'] = currObject.created
		currObject.fields['password'] = encrypt(currObject.fields['password'],currObject.created)
		
	    if 'code' in data:
		currObject.code = data['code']
		
	    if data['placeImg'] != '': 
		filepath = data.placeImg.filename.replace('\\','/') 
		ext = ((filepath.split('/')[-1]).split('.')[-1])
		fout = open(currObject.getImageDirectory()+'jpg','w')
		fout.write(data.placeImg.file.read())
		fout.close()
	    currObject.save(c,user)
	    return render.listing(c,mail,'places')
	raise web.seeother('/')
	
class WebIndex(WebObject):
    def __init(self):
	self.name = u"WebIndex"
	
    def getRender(self, mail):
	return render.index(True,c,mail)
	
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
    
    def getRender(self, mail):
	return render.listing(c,mail,'places')
	
class WebEquipments(WebObject):
    def __init__(self):
	self.name=u"WebEquipments"
	
    def getRender(self, mail):
	return render.listing(c,mail,'equipments')

class WebPlace(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebPlace"
	
    def getRender(self, id, mail):
	return render.place(c,id,mail)

	
class WebEquipment(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebEquipment"
	
    def getRender(self, id, mail):
	return render.equipment(c,id,mail)

class WebUsers(WebObject):
    def __init__(self):
	self.name=u"WebUsers"
    
    def getRender(self, mail):
	return render.listing(c,mail,'users')
	
class WebUser(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebUser"
	
    def getRender(self, id, mail):
	return render.user(c,id,mail)

class WebGroups(WebObject):
    def __init__(self):
	self.name=u"WebGroups"
    
    def getRender(self, mail):
	return render.listing(c,mail,'groups')
	
class WebGroup(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebGroup"
	
    def getRender(self, id, mail):
	return render.group(c,id,mail)
	
class WebPermission(WebObjectUpdate):
    def __init__(self):
	self.name=u"WebPermission"
	
    def getRender(seld,id,mail):
	typeobject = id.split('_')[0]
	idobject = id.split('_')[1]
	return render.permissions(c,mail,idobject,typeobject)
	
    def POST(self, id):
	mail = isConnected()
	user  = c.connectedUsers.users[mail].cuser
	if mail is not None:
	    typeobject = id.split('_')[0]
	    idobject = id.split('_')[1]
	    currObject = c.getObject(idobject, typeobject)
	    if currObject is None:
		raise web.seeother('/')
	    data = web.input(placeImg={})
	    method = data.get("method","malformed")
	    listgroups = {}
	    for k,group in currObject.groups.items():
		if k not in data:
		    currObject.deleteGroup(k,c,user)
	    for k,group in c.AllGroups.elements.items():
		if k in data:
		    currContainsGroup = currObject.containsGroup(group)
		    groupContainsCurr = group.containsGroup(currObject)
		    if ( not currContainsGroup ) and ( not groupContainsCurr ):
			listgroups[k] = group
	    currObject.groups = listgroups
	    currObject.saveGroups(c,user)
	    return render.listing(c,mail,'groups')
	return render.index(False,c,'')

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

def printinfo(user):
    print user

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
