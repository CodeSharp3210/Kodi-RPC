import xbmcgui
import xbmcaddon
import xbmcvfs
import os

addon = xbmcaddon.Addon()

class UtilityGUI(xbmcgui.WindowXMLDialog):
    def onInit(self):
        self.btn_rpc = self.getControl(101)
        self.btn_cache = self.getControl(102)
        self.btn_exit = self.getControl(103)

    def onClick(self, controlId):
        if controlId == 101:
            self.toggle_rpc()
        elif controlId == 102:
            self.pulisci_cache()
        elif controlId == 103:
            self.pulisci_log()
        elif controlId == 104:
            self.close()

    def toggle_rpc(self):
        enabled = addon.getSettingBool("rpc_enabled")
        addon.setSettingBool("rpc_enabled", not enabled)

        if enabled:
            from resources.lib.discord_rpc import stop_rpc
            stop_rpc()
            xbmcgui.Dialog().notification(
                "Clover Client",
                "RPC Disabled",
                xbmcgui.NOTIFICATION_INFO,
                1000
            )
        else:
            from resources.lib.discord_rpc import start_rpc
            xbmcgui.Dialog().notification(
                "Clover Client",
                "RPC Enabled",
                xbmcgui.NOTIFICATION_INFO,
                1000
            )
            start_rpc()

    def pulisci_log(self):
        path = xbmcvfs.translatePath("special://home/cache/")

        for root, dirs, files in os.walk(path):
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    # Usa xbmcvfs.delete invece di os.remove
                    if xbmcvfs.exists(file_path):
                        xbmcvfs.delete(file_path)
                except Exception as e:
                    xbmcgui.Dialog().notification("Clover Client", "An error occurred during this stage")
        xbmcgui.Dialog().notification("Clover Client", "Done. Logs cleaned")
        
    def pulisci_cache(self):
        path = xbmcvfs.translatePath("special://home/cache/")

        def cancella_file(path):
            dirs, files = xbmcvfs.listdir(path)
            # Cancella tutti i file nella cartella corrente
            for f in files:
                file_path = path + f
                try:
                    if xbmcvfs.exists(file_path):
                        xbmcvfs.delete(file_path)
                except Exception as e:
                    xbmcgui.Dialog().notification("Clover Client", "An error occurred during this stage")
            # Richiama ricorsivamente per tutte le sottocartelle
            for d in dirs:
                cancella_file(path + d + "/")  # Nota lo slash finale

        cancella_file(path)
        xbmcgui.Dialog().notification("Clover Client", "Done. Cache cleaned")
UtilityGUI("gui.xml", addon.getAddonInfo("path")).doModal()
del UtilityGUI
