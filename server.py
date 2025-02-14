from twisted.internet import reactor,ssl, protocol
import config
import uuid
import json
import header
import re
import log
import base64

def get(data):
    pattern = r"GET (/.*?)\s+HTTP"
    if m := re.search(pattern, data):
        return m[1]


class cl:
    clients = []
    source = None
    sourceID = None
    sent_header = []
    id3_headers = {
        "title": "None",
        "length": "0",
        "bitrate": "0"
    }

class RadioServer(protocol.Protocol):
    mount = None

    def connectionMade(self):
        if config.PyCasterMaxListeners != len(cl.clients):
            self.id = str(uuid.uuid4())
            self.peer = str(self.transport.getPeer())
            log.log(f"Client-Connected-IP: {self.peer}")
            log.log(f"Client-Connected-ID: {self.id}")
        else:
            self.transport.abortConnection()
            log.log("Client-Limit")

    def connectionLost(self, reason):
        if self.id == cl.sourceID:
            log.log(f"Source-Closed: {str(reason)}")
            cl.sourceID = None
            cl.source = None
        else:
            self.removeClient(self.id)
            log.log(f"Client-Closed-Reason: {str(reason)}")
            log.log(f"Client-Closed-IP: {self.peer}")
            log.log(f"Client-Closed-ID: {self.id}")

    def dataReceived(self, data):
        try: dct = json.loads(data)
        except: dct = {}

        if get(data) == "/":
            if not self.mount:
                self.mount = ";"
            with open("index.html", "r") as f:
                content = f.read()
            resp = "HTTP/1.1 200 OK\r\n" + header.HTTP_RESP.format(
                "text/html",
                len(content),
                content.replace("$host", self.transport.getHost().host).replace("$port", str(config.PyCasterPort)).replace("$mount", self.mount))
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/img/background.jpg":
            with open("img/background.jpg", "rb") as f:
                content = f.read()
            resp = "HTTP/1.1 200 OK\r\n" + header.HTTP_RESP.format(
                "image/jpeg",
                len(content),
                content)
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/img/content-bg.png":
            with open("img/content-bg.png", "rb") as f:
                content = f.read()
            resp = "HTTP/1.1 200 OK\r\n" + header.HTTP_RESP.format(
                "text/html",
                len(content),
                content)
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/title":
            resp = "HTTP/1.1 200 OK\r\n"+config.ORIGIN+"\r\n"+ header.HTTP_RESP.format(
                "text/plain",
                len(cl.id3_headers['title']),
                cl.id3_headers['title'])
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/listeners":
            resp = "HTTP/1.1 200 OK\r\n" + config.ORIGIN + "\r\n" + header.HTTP_RESP.format(
                "text/plain",
                len(str(len(cl.clients))),
                str(len(cl.clients)))
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/max-listeners":
            resp = "HTTP/1.1 200 OK\r\n" + config.ORIGIN + "\r\n" + header.HTTP_RESP.format(
                "text/plain",
                len(str(config.PyCasterMaxListeners)),
                str(config.PyCasterMaxListeners))
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/bitrate":
            resp = "HTTP/1.1 200 OK\r\n" + config.ORIGIN + "\r\n" + header.HTTP_RESP.format(
                "text/plain",
                len(str(cl.id3_headers['bitrate'])),
                str(cl.id3_headers['bitrate']))
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif get(data) == "/length":
            resp = "HTTP/1.1 200 OK\r\n" + config.ORIGIN + "\r\n" + header.HTTP_RESP.format(
                "text/plain",
                len(str(cl.id3_headers['length'])),
                str(cl.id3_headers['length']))
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif dct.has_key("PyCasterAuth"):
            if not cl.sourceID:
                auth = dct['PyCasterAuth']
                if auth == config.PyCasterAuth:
                    cl.source = self
                    cl.sourceID = self.id
                    event = {"login": "OK", "message": "None"}
                    event = json.dumps(event)
                    self.transport.write(event)
                    log.log("Source-Registered")
                    log.log(f"Source-ID: {self.id}")
                else:

                    event = {"login": "denied", "message": "Invalid auth"}
                    event = json.dumps(event)
                    self.transport.write(event)
                    log.log(f"Source-Login-Denied-IP: {self.peer}")
                    log.log(f"Source-Login-Denied-ID: {self.id}")

            else:
                log.log(f"Source-Exists-IP: {self.peer}")
                log.log(f"Source-Exists-ID: {self.id}")
                event = {"login": "denied", "message": "Source exists"}
                event = json.dumps(event)
                self.transport.write(event)
                self.closeCl(self.id)
        elif dct.has_key("PyCasterMount"):
            self.mount = dct['PyCasterMount']

        elif dct.has_key("info"):
            cl.id3_headers = dct["info"]

        elif dct.has_key("buffer"):
            buffer = base64.b64decode(dct['buffer'])
            self.sendClients(buffer, bin=True)

        elif not cl.source:
            content = "<b>Source not connected..</b>"
            resp = "HTTP/1.1 200 OK\r\n" + header.HTTP_RESP.format(
                "text/html",
                len(content),
                content)
            log.log(f"Client-Http-GET: {get(data)}")
            self.HTTPSendClient(resp)

        elif not self.mount:
            if get(data) not in config.pages:
                cl.clients.append(self)

        elif get(data) == self.mount:
            cl.clients.append(self)

    def removeClient(self, id):
        for client in cl.clients:
            if client.id == id:
                cl.clients.remove(client)
                if client in cl.sent_header:
                    cl.sent_header.remove(client)



    def closeCl(self, id):
        for client in cl.clients:
            if client.id == id:
                self.removeClient(id)
                client.transport.abortConnection()
                log.log(f"Server-Closed-Client: ({id}, {client.peer})")


    def HTTPSendClient(self, msg):
        log.log(f"Client-Http-Resp-ID: {self.id}")
        log.log(f"Client-Http-Resp-IP: {self.peer}")
        self.transport.write(msg)


    def sendClients(self, msg, bin=False):
        for client in cl.clients:
            if client.id == cl.sourceID:
                self.removeClient(client.id)
            if bin and client not in cl.sent_header:
                head = header.header
                head = head\
                    .replace("$title", cl.id3_headers['title'])\
                    .replace("$length", str(cl.id3_headers['length']))\
                    .replace("$listen", str(len(cl.clients)))\
                    .replace("$bitrate", str(cl.id3_headers['bitrate']))\
                    .replace("$max", str(config.PyCasterMaxListeners))
                client.transport.write("HTTP/1.1 200 OK\r\n"+bytes(head))
                cl.sent_header.append(client)
            client.transport.write(msg)
            if config.PyCasterSendLogging:
                log.log("SENT %i bytes TO %s" % (len(msg), client.id))


if __name__=="__main__":
    import sys
    key = config.PyCasterSSLKey
    cert = config.PyCasterSSLCert
    factory = protocol.Factory()
    factory.protocol = RadioServer
    if config.PyCasterSSL:
        reactor.listenSSL(config.PyCasterPort, factory,  ssl.DefaultOpenSSLContextFactory(key, cert))
    else:
        reactor.listenTCP(config.PyCasterPort, factory)

    reactor.run()

