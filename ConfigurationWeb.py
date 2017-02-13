import web
import ConfigurationELSA as elsa

render=web.template.render('templates/',base='layout')

urls = (
    '/', 'Index',
    '/index','Index',
    '/place/(.+)', 'Place',
    '/places', 'Places',
)
#Configuration Singleton ELSA
c=elsa.Configuration()
allPlaces=c.AllPieces
allPlaces.load()
allLanguages=c.AllLanguages
allLanguages.load()
print allLanguages.elements['francais']

class Index:
    def GET(self):
        return render.index()
    def POST(self):
	data = web.input(nifile={})
        method = data.get("method","malformed")
	#TODO connexion data._username_,data._password_
	return render.index()
class Places:
    def GET(self):
	return render.places(allPlaces.getListObjects())

class Place:
    def GET(self,id):
	return render.place(allPlaces.elements[str(id)].fields)
	
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
