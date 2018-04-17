#!/usr/bin/env python
# -*- coding: utf-8 -*-
import web
import ConfigurationELSA as elsa
import myuseful as useful
import traceback
import sys
import shutil
import os
import backup
import argparse
import subprocess
import json
import rrd
import time
import calendar
global c, render

def manage_cmdline_arguments():
    parser = argparse.ArgumentParser(description='Enregistrement des Lots \
                                                  pour la Sécurité Alimentaire')
    # Est interprété directement par WebPY
    parser.add_argument('port', type=int, help='Port number of the internal \
                                                web server')
    parser.add_argument('--hw-config', help='Configuration file for this \
                                             particular computer')
    return parser.parse_args()

def web_link_from_abs_path(path):
    """
    Will strip DIR_BASE from path. Intended to be used in href
    """
    return path[len(elsa.DIR_BASE):]

def getLinkForLatestBackupArchive():
    """
    Returns the web path (as in web_link_from_abs_path) of the lastest backup
    archive in the temporary web folder
    """
    list = os.listdir(elsa.DIR_WEB_TEMP)
    lastFile = None
    for f in sorted(list):
        if f.find(backup.ARCHIVE_FILE_NAME_PREFIX) >= 0:
            lastFile = f
    if lastFile is not None:
        return web_link_from_abs_path(os.path.join(elsa.DIR_WEB_TEMP, lastFile))
    else:
        return None

class WebColor():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return render.colorpicker(mail, type, id)
        return ''

class WebBackup():
    def __init(self):
        self.name = u"WebBackup"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return render.backup(mail, getLinkForLatestBackupArchive(),"")
        raise web.seeother('/')
    
    def POST(self):
        mail = isConnected()
        if mail is None:
            raise web.seeother('/')
        else:
            data = web.input()
            if data is not None and data.create_backup is not None:
                backup.create_backup_zip()
                return render.backup(mail, getLinkForLatestBackupArchive(),"backupDone")
            return render.backup(mail, getLinkForLatestBackupArchive(),"")

class WebRestore():
    def __init(self):
        self.name = u"WebRestore"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return render.backup(mail, getLinkForLatestBackupArchive(),"")
        raise web.seeother('/')
    
    def POST(self):
        mail = isConnected()
	if mail is None:
            raise web.seeother('/')
        else:
            data = web.input(zip_archive_to_restore={})
            if data is not None and 'zip_archive_to_restore' in data and data['zip_archive_to_restore'].filename:
                # replaces the windows-style slashes with linux ones.
                fpath = data['zip_archive_to_restore'].filename.replace('\\','/')
                # splits the and chooses the last part (filename with extension)
		fname = fpath.split('/')[-1]
                try:
                    fout = open(os.path.join(elsa.DIR_WEB_TEMP, fname),'w')
		    fout.write(data.zip_archive_to_restore.file.read())
                except IOError:
		    fout.close()
                    print("Error while restoring file.")
                    return render.backup(mail, getLinkForLatestBackupArchive(), "restoreError")
		fout.close()
                flags.set_restore(fname)
                raise web.seeother('/restarting')
            else:
                return render.backup(mail, getLinkForLatestBackupArchive(), "restoreEmpty")

class WebUpdateELSA():
    def __init(self):
        self.name = u"WebUpdateELSA"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return render.updateELSA(mail)
        raise web.seeother('/')
    
    def POST(self):
        mail = isConnected()
        data = web.input()
        if mail is not None and data.start_elsa_update is not None:
            flags.set_check_update(True)
            raise web.seeother('/restarting')
        else:
            raise web.seeother('/')
        
def get_list_of_active_sensors_acronyms(lang):
    list = []
    for i in c.AllSensors.elements:
        if c.AllSensors.elements[i].fields['active'] == '1':
            acronym = c.AllSensors.elements[i].get_acronym()
            if lang is None:
                list.append(acronym)
            else:
                list.append(c.AllSensors.elements[i].getName(lang) + u' [' + acronym + u']')
    return list

def get_data_points_for_grafana_api(target, lang, time_from_utc, time_to_utc):
    datapoints = []
    sensor = None
    acronym = target
    if lang is not None:
        acronym = target[target.find('[')+1 : -1]

    sensor = c.AllSensors.findAcronym(acronym)
    try:
        sensor_id = sensor.fields['s_id']
    except AttributeError:
        raise ValueError("That acronym does not exist : " + target)
    
    return {"target": target, "datapoints": rrd.get_datapoints_from_s_id(sensor_id, time_from_utc, time_to_utc)}

def get_annotation_for_grafana_api(acronyms, time_from_utc, time_to_utc):
    annotations = []
    sensors = []
    
    for i in acronyms:
        try:
            sensors = (c.AllSensors.findAcronym(i).fields['s_id'])
        except AttributeError:
            raise ValueError("That acronym does not exist : " + unicode(i))
    
    print('dsf', sensors[0], c.AllAlarmLogs.get_alarmlog_component(sensors[0],
                    calendar.timegm(time_from_utc),
                    calendar.timegm(time_to_utc))) 


class WebApiGrafana():
    def __init(self):
        self.name = u"WebApiGrafana"

    def parse_time_range(self, range):
        time_from_utc = range['from']
        time_from_utc = time_from_utc.split('.')[0]
        time_from_utc = time.strptime(time_from_utc, "%Y-%m-%dT%H:%M:%S")
        time_to_utc = time.strptime(range['to'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
        return time_from_utc, time_to_utc    
        
    def GET(self, lang='', request=''):
        # When no lang is set, WebPY inverts lang and request variables
        if request == '':
            request = lang
            lang = None
        return 'You have reached the / of ELSA\'s API for Grafana'

    def POST(self, lang='', request=''):
        # When no lang is set, WebPY inverts lang and request variables
        if request == '':
            request = lang
            lang = None
        try:
            data=json.loads(unicode(web.data()))
        except ValueError:
            print('Unable to parse JSON from Grafana. Ignoring.')
            return None

        if request=='search':
            return json.dumps(get_list_of_active_sensors_acronyms(lang))
        elif request=='query':
            time_from_utc, time_to_utc = self.parse_time_range(data['range'])
            targets = []
            for elem in data['targets']:
# .replace removes all '\' in the target name. Fixes a grafana/simple-json bug.
                targets.append(elem['target'].replace('\\', ''))
            out = []
            for elem in targets:
                out.append(get_data_points_for_grafana_api(elem, lang, time_from_utc, time_to_utc))
            return json.dumps(out)
        elif request=='annotations':
            time_from_utc, time_to_utc = self.parse_time_range(data['range'])
            name = data['annotation']['name']
            enable = data['annotation']['enable']
            query = json.loads(data['annotation']['query'])
            return json.dumps(get_annotation_for_grafana_api(query,
                                                             time_from_utc,
                                                             time_to_utc))
        else:
            return 'Error: Invalid url requested'
    

class WebRestarting():
    global app
    def __init(self):
        self.name = u"WebRestarting"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            app.stop()
            # sys.exit()
            return render.restarting(mail)
        raise web.seeother('/')
    
class WebDisconnect():
    def GET(self):
        mail = isConnected()
        if mail is not None:
            c.connectedUsers.disconnect(mail)
        raise web.seeother('/')

class WebPermission():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            if len(id.split('/')) > 1:
                context = id.split('/')[-1]
                id = id.split('/')[0]
            else:
                context = ''
            return render.permission(mail, type, id, context)
        return ''


class WebModal():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return render.modal(mail, type, id)
        return ''


class WebFullEntry():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return render.fullentry(mail, type, id)
        return ''


class WebList():
    def __init__(self):
        self.name = u"WebList"
    
    def GET(self, type):
        id = ''
        data = web.input(nifile={})
        if 'status' in data:
            id = data['status']
        mail = isConnected()
        if mail is not None:
            if type in 'abcpehsmugugrgftmdmvm' and type != 't' and type != 'f':
                return self.getRender(type, mail, id)
            else:
                return render.notfound()
        raise web.seeother('/')

    def POST(self, type):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            data = web.input(placeImg={})
            if 'quantity' in data:
                try:
                    if type == 'b':
                        count = 1
                        borne = int(data['quantity'])
                        elem = c.AllBatches.elements[data['batch'].split('_')[
                            1]]
                        try:
                            name = int(
                                elem.fields['acronym'][elem.fields['acronym'].rfind('_')+1:])
                        except:
                            name = 0
                        while count <= borne:
                            elem.clone(user, (name + count))
                            count += 1
                    return self.getRender(type, mail)
                except:
                    raise render.notfound()
        raise web.seeother('/')

    def getRender(self, type, mail, id=''):
        return render.listing(mail, type, id)


class WebItem():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            try:
                return render.item(type, id, mail)
            except:
                return render.notfound()
        raise web.seeother('/')


class WebEdit():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id, mail, '', '')
        raise web.seeother('/')

    def POST(self, type, id, context=None):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            currObject = c.getObject(id, type)
            infoCookie = mail + ',' + user.fields['password']
            data = web.input(placeImg={})
            method = data.get("method", "malformed")
            update_cookie(infoCookie)
            if currObject is None:
                raise web.seeother('/')
            cond = currObject.validate_form(data, c, user.fields['language'])
            if cond is True:
                currObject.set_value_from_data(data, c, user)
                if 'a_id' in data:
                    if len(data['a_id']) > 0:
                        c.AllAlarms.elements[data['a_id']
                                             ].launch_alarm(currObject, c)
                if type not in 'tdv':
                    raise web.seeother('/item/'+type+'_'+currObject.getID())
                else:
                    if currObject.get_type() == 'v':
                        elemtype = 'b'
                        elemid = currObject.fields['dest']
                    elif currObject.get_type() == 't':
                        elemtype = currObject.fields['object_type']
                        elemid = currObject.fields['object_id']
                    elif currObject.get_type() == 'd':
                        elemtype = currObject.fields['object_type']
                        elemid = currObject.fields['object_id']
                    raise web.seeother('/find/'+type+'/'+elemtype+'_'+elemid)
            else:
                if id == 'new':
                    currObject.delete(c)
                return self.getRender(type, id, mail, cond, data)
        raise web.seeother('/')

    def getListing(self, mail, type, id=''):
        return render.listing(mail, type, id)

    def getRender(self, type, id, mail, errormess, data, context=''):
        if type in 'hpebcsmagugrgfutmdmvm' and type != 'g' and type != 'f' and type != 'd' and type != 'v'and type != 't':
            if type == 'p':
                return render.place(id, mail, errormess, data, context)
            elif type == 'e':
                return render.equipment(id, mail, errormess, data, context)
            elif type == 'b':
                return render.batch(id, mail, errormess, data, context)
            elif type == 'c':
                return render.container(id, mail, errormess, data, context)
            elif type == 's':
                return render.sensor(id, mail, errormess, data)
            elif type == 'm':
                return render.measure(id, mail, errormess, data)
            elif type == 'a':
                return render.alarm(id, mail, errormess, data)
            elif type == 'gu':
                return render.group(type, id, mail, errormess, data)
            elif type == 'gr':
                return render.group(type, id, mail, errormess, data)
            elif type == 'gf':
                return render.group(type, id, mail, errormess, data)
            elif type == 'h':
                return render.group(type, id, mail, errormess, data, context)
            elif type == 'u':
                return render.user(id, mail, errormess, data, context)
            elif type == 'tm':
                return render.transfermodel(id, mail, errormess, data, context)
            elif type == 'dm':
                return render.manualdatamodel(id, mail, errormess, data, context)
            elif type == 'vm':
                return render.pouringmodel(id, mail, errormess, data, context)
        elif type == 't':
            return render.transfer(id, mail, errormess, context)
        elif type == 'd':
            return render.manualdata(id, mail, errormess, context)
        elif type == 'v':
            return render.pouring(id, mail, errormess, context)


class WebCreate(WebEdit):
    def GET(self, type):
        mail = isConnected()
        if mail is not None:
            if len(type.split('/')) == 1:
                return self.getRender(type, 'new', mail, '', '')
            else:
                return self.getRender(type.split('/')[0], 'new', mail, '', '', type.split('/')[-1])
        raise web.seeother('/')

    def POST(self, type):
        if len(type.split('_')) > 1:
            return WebEdit.POST(self, type.split('/')[0], 'new', type.split('/')[-1])
        else:
            return WebEdit.POST(self, type.split('/')[0], 'new')


class WebControl():
    def GET(self, idbatch, idcontrol):
        mail = isConnected()
        if mail is not None:
            return render.control(idbatch, idcontrol, mail, '')
        raise web.seeother('/')

    def POST(self, idbatch, idcontrol, context=None):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            method = data.get("method", "malformed")
            currObject = c.getObject(idcontrol, 'h')
            cond = currObject.validate_control(data, user.fields['language'])
            if cond is True:
                currObject.create_control(data, user)
                raise web.seeother('/find/h/b_' + str(idbatch))
            else:
                return render.control(idbatch, idcontrol, mail, cond)
        raise web.seeother('/')


class WebFind():
    def GET(self, type, id1, id2):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id1, id2, mail)
        raise web.seeother('/')

    def POST(self, type, id1, id2):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            if type == 'h':
                if 'checkpoint' in data:
                    raise web.seeother('/control/b_'+id2 +
                                       '/h_'+data['checkpoint'])
                raise web.seeother('/item/b_'+id2)
        raise web.seeother('/')

    def getRender(self, type, id1, id2, mail):
        try:
            if type == 'related' and id1 == 'm':
                return render.listingmeasures(id2, mail)
            elif type == 'd'and id1 in 'pceb':
                return render.itemdata(id1, id2, mail)
            elif type == 't' and id1 in 'ceb':
                return render.itemtransfers(id1, id2, mail)
            elif type == 'v' and id1 in 'ecb':
                return render.listingpourings(id2, mail)
            elif type == 'related'and ('g' in id1 or id1 == 'h'):
                return render.listinggroup(id1, id2, mail)
            elif type == 'related':
                return render.listingcomponent(id1, id2, mail)
            elif type == 'h':
                return render.listingcontrol(id1, id2, mail)
            else:
                return render.notfound()
        except:
            traceback.print_exc()
            return render.notfound()


class WebGraphic():
    def __init__(self):
        self.name = u"WebGraph"

    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            objects = c.findAllFromType(type)
            if id in objects.elements.keys() and type in 'scpem':
                return render.listinggraphics(mail, type, id)
            return render.notfound()
        raise web.seeother('/')


class WebIndex():
    def __init(self):
        self.name = u"WebIndex"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return self.getRender(mail)
        return render.index(False, '')

    def POST(self):
        data = web.input(nifile={})
        # method = data.get("method","malformed")
        connectedUser = connexion(data._username_, data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + \
                connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)
            return render.index(True, data._username_)
        return render.index(False, '')

    def getRender(self, mail):
        return render.index(True, mail)


class WebBarcode():
    def __init__(self):
        self.name = u"WebBarcode"

    def GET(self, id=""):
        mail = isConnected()
        if mail is not None:
            try:
                data = web.input()
                if 'barcode' in data:
                    id = data['barcode']
                return self.getRender(id, mail)
            except:
                return self.getRender(id, mail, 'notfound')
        raise web.seeother('/')

    def getRender(self, id, mail, errormess=''):
        return render.barcode(mail, id, errormess)

    def getListing(self, mail):
        return render.listing(mail, 'places')


class getRRD():
    def GET(self, filename):
        try:
            f = open(elsa.DIR_RRD + filename)
            return f.read()
        except IOError:
            web.notfound()


class getCSV():
    def GET(self, filename):
        try:
            f = open(elsa.DIR_CSV + filename)
            return f.read()
        except IOError:
            web.notfound()


class WebMonitoring():
    def __init__(self):
        self.name = u"WebMonitoring"

    def GET(self):
        mail = isConnected()
        if mail is not None:
            return self.getRender(mail)
        return render.index(False, '')

    def POST(self):
        data = web.input(nifile={})
        # method = data.get("method","malformed")
        connectedUser = connexion(data._username_, data._password_)
        if connectedUser is not None:
            infoCookie = data._username_ + ',' + \
                connectedUser.fields['password']
            update_cookie(infoCookie)
            c.connectedUsers.addUser(connectedUser)
            return render.index(True, data._username_)
        return render.index(False, '')

    def getRender(self, mail):
        return render.monitoring(mail)


class WebListing():
    def __init__(self):
        self.name = u"WebListing"

    def GET(self, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(id, mail, '')
        return render.index(False, '')

    def getRender(self, id, mail, error):
        typeobject = id.split('_')[0]
        idobject = id.split('_')[1]
        if typeobject in 'pceb':
            return render.listingcomponent(mail, idobject, typeobject)
        elif typeobject == 'g':
            return render.listinggroup(mail, idobject)
        elif typeobject == 'm':
            return render.listingmeasures(mail, idobject)
        else:
            return render.notfound()


class WebExport():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id, mail)
        return render.index(False, '')

    def POST(self, type, id):
        mail = isConnected()
        user = c.connectedUsers.users[mail].cuser
        if mail is not None:
            infoCookie = mail + ',' + user.fields['password']
            update_cookie(infoCookie)
            data = web.input(placeImg={})
            cond = {}
            cond['alarm'] = True if 'alarm' in data else False
            cond['manualdata'] = True if 'manualdata' in data else False
            cond['transfer'] = True if 'transfer' in data else False
            cond['pouring'] = True if 'pouring' in data else False
            cond['specialvalue'] = True if 'specialvalue' in data else False
            cond['valuesensor'] = True if 'valuesensor' in data else False
            cond['acronym'] = True if 'acronym' in data else False
            method = data.get("method", "malformed")
            elem = c.findAllFromType(data['element'].split(
                '_')[0]).elements[data['element'].split('_')[1]]
            tmp = elsa.ExportData(c, elem, cond, user)
            tmp.create_export()
            if "download" in data:
                tmp.write_csv()
                raise web.seeother('/export/'+str(type) +
                                   '_'+str(id)+'/exportdata.csv')
            else:
                user.exportdata = tmp
                raise web.seeother('/datatable/'+str(type)+'_'+str(id))
        return render.index(False, '')

    def getRender(self, type, id, mail):
        try:
            if type in 'cpeb':
                return render.exportdata(mail, type, id)
            else:
                return render.notfound()
        except:
            return render.notfound()


class WebDataTable():
    def GET(self, type, id):
        mail = isConnected()
        if mail is not None:
            return self.getRender(type, id, mail)
        return render.index(False, '')

    def getRender(self, type, id, mail):
        # try:
        if type in 'cpeb':
            return render.datatable(mail, type, id)
        else:
            return render.notfound()
        """except :
            return render.notfound()"""


class WebDownloadData():
    def GET(self, id1, id2, filename):
        try:
            web.header('Content-Disposition',
                       'attachment; filename="'+str(filename)+'"')
            web.header('Content-type', 'text/tab-separated-values')
            web.header('Content-transfer-encoding', 'binary')
            f = open(elsa.DIR_CSV + filename)
            return f.read()
        except IOError:
            web.notfound()


def connexion(username, password):
    user = c.AllUsers.getUser(username)
    if user is not None:
        cryptedPassword = useful.encrypt(password, user.fields['registration'])
        if user.checkPassword(cryptedPassword) is True:
            return user
    return None


def isConnected():
    infoCookie = web.cookies().get('webpy')
    if infoCookie is not None:
        infoCookie = infoCookie.split(',')
        if c.connectedUsers.isConnected(infoCookie[0], infoCookie[1]) is True:
            return infoCookie[0]
    return None


def notfound():
    return web.notfound(render.notfound())


def update_cookie(infoCookie):
    web.setcookie('webpy', infoCookie, expires=9000)

def cleanup_web_temp_dir():
    try:
        shutil.rmtree(elsa.DIR_WEB_TEMP)
    except OSError, e:
        print ("Error: %s - %s." % (e.filename,e.strerror))
    finally:
        if not os.path.exists(elsa.DIR_WEB_TEMP):
            os.makedirs(elsa.DIR_WEB_TEMP)


def start_update():
    print("Debut de la mise à jour d'ELSA avec Git")
    try:
        subprocess.check_call("git pull", shell=True) #, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError:
        print("Update error. Please update manually.")
    finally:
        print("Fin du processus de mise à jour")

def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """
    elsa._lock_socket.close()
    python = sys.executable
    args = sys.argv
    args[0] = os.path.join(elsa.DIR_BASE, os.path.basename(sys.argv[0]))
    os.execl(python, python, *args)

class end_activities_flags:
    """
    An object that holds some flags until just before the end of the program.
    Intended to launch things when we want to ELSA to be in a coherent state.
    """
    def __init__(self):
        self._check_update = False
        self._restart = False
        self._restore = False
    
    def set_restore(self, fname):
        self._restore = fname

    def set_check_update(self, value):
        if value == False:
            self._check_update = False
        elif value == True:
            self._check_update = True
        else:
            raise("Invalid value received : expected bool")

    def set_restart(self):
        self._restart = True
    
    def launch_end_activities(self):
        if self._restore:
            if not backup.restore_from_zip(self._restore): #returns False if restore did not work but no way to alert the user !
                print ("INVALID RESTORE FILE")
            self.set_restart()

        if self._check_update:
            start_update()
            self.set_restart()
	
        if self._restart:
	    restart_program() 
        

c = None
wsgiapp = None
flags = end_activities_flags()
app = None

def main():
    # restart_program()
    args = manage_cmdline_arguments()
    cleanup_web_temp_dir()

    global c, wsgiapp, render, app
    try:
        web.config.debug = False
        # Configuration Singleton ELSA
        if 'config' in args:
            c = elsa.Configuration(args.config)
        else:
            c = elsa.Configuration(None)
        c.load()
        web.template.Template.globals['c'] = c
        web.template.Template.globals['useful'] = useful
        layout = web.template.frender(elsa.TEMPLATES_DIR+'/layout.html')
        render = web.template.render(elsa.TEMPLATES_DIR, base=layout)
        urls = (
            '/', 'WebIndex',
            '/index', 'WebIndex',
            '/edit/(.+)_(.+)', 'WebEdit',
            '/item/(.+)_(.+)', 'WebItem',
            '/create/(.+)', 'WebCreate',
            '/monitoring/', 'WebMonitoring',
            '/rrd/(.+)', 'getRRD',
            '/csv/(.+)', 'getCSV',
            '/list/(.+)', 'WebList',
            '/graphic/(.+)_(.+)', 'WebGraphic',
            '/barcode/(.+)', 'WebBarcode',
            '/barcode/', 'WebBarcode',
            '/modal/(.+)_(.+)', 'WebModal',
            '/color/(.+)_(.+)', 'WebColor',
            '/fullentry/(.+)_(.+)', 'WebFullEntry',
            '/export/(.+)_(.+)/(.+)', 'WebDownloadData',
            '/export/(.+)_(.+)', 'WebExport',
            '/datatable/(.+)_(.+)', 'WebDataTable',
            '/find/(.+)/(.+)_(.+)', 'WebFind',
            '/permission/(.+)_(.+)', 'WebPermission',
            '/control/b_(.+)/h_(.+)', 'WebControl',
            '/disconnect', 'WebDisconnect',
            '/backup', 'WebBackup',
            '/restore', 'WebRestore',
            '/updateELSA', 'WebUpdateELSA',
            '/restarting', 'WebRestarting',
            '/api/grafana/([^/]*)/{0,1}(.*)', 'WebApiGrafana'
        )
        app = web.application(urls, globals())
        app.notfound = notfound
        app.run()
        # wsgiapp = app.wsgifunc()
    except:
        traceback.print_exc(file=sys.stdout)
    finally:
        print 'fin des threads'
        if c:
            c.isThreading = False
            c.UpdateThread.join()
            c.RadioThread.join()
        
        flags.launch_end_activities()

        print 'Exit system'


if __name__ == "__main__":
    main()
