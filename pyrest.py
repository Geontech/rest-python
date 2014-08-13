#!/usr/bin/env python
import os,sys
cwd = os.getcwd()

# from model import domain
from model.mydomain import MyDomain
from model.mydomain import scan_domains
import tornado.ioloop
import tornado.web
import tornado.websocket
import threading


class OdmEvents(tornado.websocket.WebSocketHandler):
    def open(self):
        self.odmContainer = domain.odmStreamHandler(self)
        self._runThread = threading.Thread(target=self.odmContainer.thread_function)
        self._runThread.setDaemon(True)
        self._runThread.start()

    def on_message(self, message):
        pass

    def on_close(self):
        self.odmContainer.closeOdmStream()


class Main(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/domain')


class JsonHandler(tornado.web.RequestHandler):
    def _render_json(self, resp):
        self.set_header("Content-Type", "application/json; charset='utf-8'")
        self.write(resp)


class Domain(JsonHandler):
    def get(self, domain_name=None):
        # if domain_name:
        #     dom = MyDomain(str(domain_name))
        #     info = dom.info()
        # else:
        #     info = {'domains': domain.scan_domains()}
        # self._render_json(info)

        domains = scan_domains()
        if len(domains) == 1:
            return self.redirect('/domain/'+domains[0])
        return 'Select the domain:'+str(domains)


class SingleDomain(tornado.web.RequestHandler):
    def get(self, domain_name):
        # domain.connectToDomain(domain_name)
        return self.render('templates/domain.html', name=domain_name)


class DomainProps(JsonHandler):
    def get(self, domain_name, prop_name=None):
        dom = MyDomain(str(domain_name))
        info = dom.info()

        if prop_name:
            value = None
            for item in info['domMgr']:
                if 'prop' in item and item['prop']['name'] == prop_name:
                    value = item['prop']

            if value:
                self._render_json(value)
            else:
                self._render_json({'error': "Could not find prop"})
        else:
            ret_seq = []
            items = info['domMgr']
            for item in items:
                for entry in item:
                    if entry == 'prop':
                        ret_seq.append(item[entry])
                        break

            self._render_json({'props': ret_seq})


class DeviceManagers(JsonHandler):
    def get(self, domain_name, dev_mgr_name=None):
        dom = MyDomain(str(domain_name))

        if dev_mgr_name:
            info = dom.device_manager_info(dev_mgr_name)
        else:
            info = dom.device_managers()

        self._render_json(info)


class Applications(JsonHandler):
    def get(self, domain_name, app_id=None):
        dom = MyDomain(str(domain_name))

        if app_id:
            info = dom.app_info(app_id)
        else:
            info = dom.apps()

        self._render_json(info)


class AvailableApplications(JsonHandler):
    def get(self, domain_name):
        dom = MyDomain(str(domain_name))
        apps = dom.available_apps()

        self._render_json(apps)


class LaunchApplication(JsonHandler):
    def get(self, domain_name):
        app_name = self.get_argument("waveform")
        dom = MyDomain(str(domain_name))
        info = dom.launch(app_name)

        self._render_json(info)


class ReleaseApplication(JsonHandler):
    def get(self, domain_name):
        app_id = self.get_argument("waveform")
        dom = MyDomain(str(domain_name))
        info = dom.release(app_id)

        self._render_json(info)

# class Service(tornado.web.RequestHandler):
#     def get(self, domainname, devmgrname, svcname):
#         resp=domain.retrieveSvcInfo(domainname,devmgrname,svcname)
#
#         self.set_header("Content-Type", "application/json; charset='utf-8'")
#         self.write(resp)
#
#
# class DevMgrProp(tornado.web.RequestHandler):
#     def get(self, domainname, devmgrname, propname):
#         resp=domain.retrieveDevMgrProp(domainname,devmgrname,propname)
#
#         self.set_header("Content-Type", "application/json; charset='utf-8'")
#         self.write(resp)


class Devices(JsonHandler):
    def get(self, domain_name, dev_mgr_name, dev_id=None):
        dom = MyDomain(str(domain_name))

        if dev_id:
            info = dom.device_info(dev_mgr_name, dev_id)
        else:
            info = dom.devices(dev_mgr_name)

        self._render_json(info)

# class Services(tornado.web.RequestHandler):
#     def get(self, domainname, devmgrname):
#         resp=domain.retrieveSvcs(domainname,devmgrname,svcname)
#
#         self.set_header("Content-Type", "application/json; charset='utf-8'")
#         self.write(resp)
#
#
# class DevMgrProps(tornado.web.RequestHandler):
#     def get(self, domainname, devmgrname):
#         resp=domain.retrieveDevMgrProps(domainname,devmgrname,propname)
#
#         self.set_header("Content-Type", "application/json; charset='utf-8'")
#         self.write(resp)


class Component(JsonHandler):
    def get(self, domain_name, app_id, comp_id):
        dom = MyDomain(str(domain_name))
        info = dom.comp_info(app_id, comp_id)

        self._render_json(info)


application = tornado.web.Application([
    (r"/", Main),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": cwd+"/static"}),
    (r"/domain/?", Domain),
    (r"/domain/([^/]+)/?", SingleDomain),
    (r"/domain/([^/]+)/info/?", Domain),
    (r"/domain/([^/]+)/props/?", DomainProps),
    (r"/domain/([^/]+)/props/([^/]+)", DomainProps),
    (r"/domain/([^/]+)/applications/?", Applications),
    (r"/domain/([^/]+)/applications/([^/]+)", Applications),
    (r"/domain/([^/]+)/launch_app", LaunchApplication),
    (r"/domain/([^/]+)/release_app", ReleaseApplication),
    (r"/domain/([^/]+)/applications/([^/]+)/([^/]+)", Component),
    (r"/domain/([^/]+)/devicemanagers/?", DeviceManagers),
    (r"/domain/([^/]+)/devicemanagers/([^/]+)", DeviceManagers),
    (r"/domain/([^/]+)/devicemanagers/([^/]+)/devs/([^/]+)", Devices),
    (r"/domain/([^/]+)/devicemanagers/([^/]+)/devs/?", Devices),
    # (r"/domain/([^/]+)/devicemanagers/([^/]+)/svcs/([^/]+)", Service),
    # (r"/domain/([^/]+)/devicemanagers/([^/]+)/svcs/?", Services),
    # (r"/domain/([^/]+)/devicemanagers/([^/]+)/props/([^/]+)", DevMgrProp),
    # (r"/domain/([^/]+)/devicemanagers/([^/]+)/props/?", DevMgrProps),
    (r"/domain/([^/]+)/availableapps/?", AvailableApplications),
    (r"/odmEvents", OdmEvents),
])

# domain.initialize(application)

if __name__ == '__main__':
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

