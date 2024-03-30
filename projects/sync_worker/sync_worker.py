import logging
import threading

from models.sync import Sync

class SyncWorker(threading.Thread):

    def __init__(self, generalconfig, hostconfig, db):
        logging.info("SYNC SETUP: create sync worker for Host id {h[hostid]} at location {h[url]}".format(h=hostconfig))

        self.hostid = hostconfig.get('hostid')
        self.interval = hostconfig.get('interval', 300)
        self.url = hostconfig.get('url')
        self.db = db

        threading.Thread.__init__(self)
        self._stopped = threading.Event()


    def run(self):
        while True:
            if self._stopped.isSet():
                return

            self.sync()
            self._stopped.wait(self.interval)


    def stop(self):
        self._stopped.set()


    def sync(self):
        logging.debug("now sync to host {s.hostid} at {s.url}".format(s=self))

        sync = Sync()
        sync.find_unsynced_rows(self.hostid, sdb=self.db)


    @classmethod
    def create_workers(cls, config):
        workers = []

        for host in config.get('hosts'):
            newworker = cls(config, host)

            workers.append(newworker)

            newworker.run()
