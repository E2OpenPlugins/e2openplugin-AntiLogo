from . import _
from Screens.Screen import Screen
from Screens.InfoBar import InfoBar
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Screens.InfoBar import InfoBar
from Plugins.Plugin import PluginDescriptor

from enigma import ePoint, eSize, getDesktop, iPlayableService

import os
import xml.etree.cElementTree as xml

# Global variables
configfilename = "/etc/enigma2/antilogo.xml"
defaultconfig = '<?xml version="1.0" encoding="iso-8859-1"?>\n<services enabled="True"/>\n'
config = None
services = None
display = None

# The global dirty flag is used to detect a change in service while
# our menu is open. The user can't do that, but the system can. E.g.
# A recording might start while the menu is open. The service to be
# recorded has a conflict with the current service but an alternative
# is available without conflict. In that case enigma will change the
# service without user intervention. But since our menu is open we will
# have invalid data to work with and we might easliy crash the system.
dirty = False

FHD = False
if getDesktop(0).size().width() >= 1920:
	FHD = True

#Global functions
def load(filename, defaultfile):
	doublefault = False
	xmlobject = None
	root = None
	while root is None:
		try:
			xmlobject = xml.parse(filename)
			root = xmlobject.getroot()
		except Exception:
			if doublefault:
				break
			configFile = open(filename, "w")
			configFile.write(defaultfile)
			configFile.close()
			doublefault = True
	return (xmlobject, root)

def write(xmlobject, filename):
	xmlobject.write(filename, encoding="iso-8859-1")

def getEnabled(services):
	return services.get('enabled') == "True"

def setEnabled(services, value):
	services.set('enabled', str(value))

def getService(services, ref):
	for service in services:
		if service.get('ref') == ref:
			return service
	return None

def createService(services, ref, name):
	newService = xml.Element("service", {'name': name, 'ref': ref})
	if newService not in services:
		services.append(newService)
	return newService

def newPreset(x, y, width, height, color):
	return xml.Element("preset", {'x': '%i' % x, 'y': '%i' % y, 'width': '%i' % width, 'height': '%i' % height, 'color': '%i' % color})

def getPosition(preset):
	return [int(preset.get("x")), int(preset.get("y"))]

def getSize(preset):
	return [int(preset.get("width")), int(preset.get("height"))]

def getColor(preset):
	return int(preset.get("color"))

# Initialisation
(config, services) = load(configfilename, defaultconfig)

# Classes
class AntiLogoScreen(Screen):
	def __init__(self, session, size, position, color, border=False):
		self.session = session
		self.size = size
		self.position = position
		self.color = color
		self.border = border
		if self.border:
			borderStr = ""
		else:
			borderStr = "flags=\"wfNoBorder\""
		colorStr = "backgroundColor=\"#%s000000\"" % '{0:02X}'.format(self.color << 4)
		self.skin = "<screen title=\"logo\" position=\"%i,%i\" size=\"%i,%i\" %s %s/>" %(position[0], position[1], size[0], size[1], colorStr, borderStr)
		Screen.__init__(self, session)

	def move(self):
		self.instance.move(ePoint(self.position[0], self.position[1]))

	def resize(self):
		self.instance.resize(eSize(*(self.size[0], self.size[1])))

class AntiLogoBase(AntiLogoScreen):
	def __init__(self, session, screen):
		AntiLogoScreen.__init__(self, session, screen.size, screen.position, screen.color, screen.border)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions"],
		{
			"ok": self.go,
			"back": self.go,
			"menu": self.go,
			"down": self.down,
			"up": self.up,
			"left": self.left,
			"right": self.right,
			}, -1)

class AntiLogoMove(AntiLogoBase):
	def __init__(self, session, screen0, screen1, step):
		self.screen0 = screen0
		self.screen1 = screen1
		self.step = step
		screen1.hide()
		AntiLogoBase.__init__(self, session, screen0)

	def go(self):
		self.screen0.move()
		self.screen1.move()
		self.screen1.show()
		self.close()

	def up(self):
		self.position[1] -= self.step
		self.move()

	def down(self):
		self.position[1] += self.step
		self.move()

	def left(self):
		self.position[0] -= self.step
		self.move()

	def right(self):
		self.position[0] += self.step
		self.move()

class AntiLogoResize(AntiLogoBase):
	def __init__(self, session, screen0, screen1, step):
		self.screen0 = screen0
		self.screen1 = screen1
		self.step = step
		screen1.hide()
		AntiLogoBase.__init__(self, session, screen0)

	def go(self):
		self.screen0.resize()
		self.screen1.resize()
		self.screen1.show()
		self.close()

	def up(self):
		self.size[1] -= self.step
		self.resize()

	def down(self):
		self.size[1] += self.step
		self.resize()

	def left(self):
		self.size[0] -= self.step
		self.resize()

	def right(self):
		self.size[0] += self.step
		self.resize()

class AntiLogoColor(AntiLogoBase):
	def __init__(self, session, list0, list1, index):
		self.session = session
		self.list0 = list0
		self.list1 = list1
		self.index = index
		list1[index].hide()
		AntiLogoBase.__init__(self, session, list0[index])

	def go(self):
		self.session.deleteDialog(self.list0[self.index])
		self.session.deleteDialog(self.list1[self.index])
		self.list0[self.index] = self.session.instantiateDialog(AntiLogoScreen, size=self.size, position=self.position, color=self.color)
		self.list1[self.index] = self.session.instantiateDialog(AntiLogoScreen, size=self.size, position=self.position, color=self.color, border=True)
		self.list1[self.index].show()
		self.close(-1)

	def up(self):
		if self.color < 15:
			self.color += 1
			self.close(self.color)

	def down(self):
		if self.color > 0:
			self.color -= 1
			self.close(self.color)

	def left(self):
		pass

	def right(self):
		pass

class AntiLogoDisplay(Screen):

	def __init__(self, session):
		desktop_size = getDesktop(0).size()
		AntiLogoDisplay.skin = "<screen name=\"AntiLogoDisplay\" position=\"0,0\" size=\"%d,%d\" flags=\"wfNoBorder\" zPosition=\"-1\" backgroundColor=\"transparent\" />" %(desktop_size.width(), desktop_size.height())
		Screen.__init__(self, session)
		self.session = session
		self.service = None
		self.dlgs = [ ]
		self.infobars = [ ]

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__evServiceStart,
				iPlayableService.evEnd: self.__evServiceEnd
			})

		# this would be the current infobar singleton
		# it would be None most likely on sessionstart
		# but we should not depend on that.
		self.infobarOpened(InfoBar.instance)
		InfoBarBase.connectInfoBarOpened(self.infobarOpened)
		InfoBarBase.connectInfoBarClosed(self.infobarClosed)

	def destroy(self):
		InfoBarBase.disconnectInfoBarOpened(self.infobarOpened)
		InfoBarBase.disconnectInfoBarClosed(self.infobarClosed)
		for infobar in self.infobars:
			self.infobarClosed(infobar)
		self.serviceEnd()

	def infobarOpened(self, infobar):
		if infobar:
			if not infobar in self.infobars:
				self.infobars.append(infobar)
			if not self.hide in infobar.onShow:
				# great, we can do this. Actually it should be a protected access
				infobar.onShow.append(self.hide)
				infobar.onHide.append(self.show)

	def infobarClosed(self, infobar):
		if infobar:
			if self.hide in infobar.onShow:
				infobar.onShow.remove(self.hide)
				infobar.onHide.remove(self.show)

	def __evServiceStart(self):
		self.serviceStart()

	def serviceStart(self):
		global services, dirty
		dirty = True
		if not self.session.nav.getCurrentService() or not self.session.nav.getCurrentlyPlayingServiceReference():
			return
		name = self.session.nav.getCurrentService().info().getName()
		ref = self.session.nav.getCurrentlyPlayingServiceReference().toString()
		# try to get name and ref from recording
		recmeta = self.session.nav.getCurrentlyPlayingServiceReference().getPath() + '.meta'
		if os.path.isfile(recmeta):
			with open(recmeta) as f:
				ref, name = f.readline().rsplit(':', 1)
		self.dlgs = []
		self.service = getService(services, ref)
		if self.service is not None:
			for preset in list(self.service):
				position = getPosition(preset)
				size = getSize(preset)
				color = getColor(preset)
				dlg = self.session.instantiateDialog(AntiLogoScreen, size=size, position=position, color=color)
				dlg.show()
				self.dlgs.append(dlg)
		else:
			self.service = createService(services, ref, name)

	def __evServiceEnd(self):
		self.serviceEnd()

	def serviceEnd(self):
		global dirty
		dirty = True
		for dlg in self.dlgs:
			self.session.deleteDialog(dlg)
		self.dlgs = []
		self.service = None

	def show(self):
		for dlg in self.dlgs:
			dlg.show()

	def hide(self):
		for dlg in self.dlgs:
			dlg.hide()

class AntiLogoMain(Screen):
	def __init__(self, session):
		global config, services, configfilename, defaultconfig, display, dirty
		desktop_size = getDesktop(0).size()
		AntiLogoMain.skin = "<screen name=\"AntiLogoMain\" position=\"0,0\" size=\"%d,%d\" flags=\"wfNoBorder\" zPosition=\"-1\" backgroundColor=\"transparent\" />" %(desktop_size.width(), desktop_size.height())
		Screen.__init__(self, session)
		self.session = session
		if display is None:
			display = session.instantiateDialog(AntiLogoDisplay)
			display.serviceStart()
#		This is the optimistic approach since an inadvertent change of service is very unlikely.
#		We might loose the work on the current service, though.
		dirty = False
		self.dlgs = []
		for dlg in display.dlgs:
			dlgWithBorder = session.instantiateDialog(AntiLogoScreen, size=dlg.size, position=dlg.position, color=dlg.color, border=True)
			self.dlgs.append(dlgWithBorder)

	def close(self):
		for dlg in self.dlgs:
			self.session.deleteDialog(dlg)
		self.dlgs = []
		super(AntiLogoMain, self).close()

	def openMenu(self):
		global display
		self.session.openWithCallback(self.menuCallback, AntiLogoMenu, display, self.dlgs)

	def menuCallback(self, code):
		global display, config, services, configfilename
		enabled = True
		if code == 1:
			display.destroy()
			self.session.deleteDialog(display)
			del display
			display = None
			enabled= False
		setEnabled(services, enabled)
		self.close()

class AntiLogoMenu(Screen):
	def __init__(self, session, display, list):
		self.session = session
		self.list = list
		self.display = display
		self.index = len(list) - 1
		self.steplist = (1, 2, 5, 10, 20, 50, 100, 200)
		self.stepindex = 2
		self.activate()
		if FHD:
			ss ="<screen position=\"center,center\" size=\"285,450\" title=\"AntiLogo\" >"
			ss +="<widget name=\"menu\" position=\"23,23\" size=\"240,450\" scrollbarMode=\"showOnDemand\" font=\"Regular;32\" itemHeight=\"41\" />"
		else:
			ss ="<screen position=\"center,center\" size=\"190,300\" title=\"AntiLogo\" >"
			ss +="<widget name=\"menu\" position=\"15,15\" size=\"160,300\" scrollbarMode=\"showOnDemand\" />"
		ss +="</screen>"
		self.skin = ss

		self["menu"] = MenuList(
						[
						(_("add"), self.add),
						(_("move"), self.move),
						(_("resize"), self.resize),
						(_("alpha"), self.color),
						(_("step +"), self.stepUp),
						(_("step -"), self.stepDown),
						(_("remove"), self.remove),
						(_("next"), self.next),
						(_("stop"), self.stop)
						])
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
						{
						"ok": self.go,
						"back": self.exit,
						}, -1)
		Screen.__init__(self, session)

	def close(self, code):
		self.deActivate()
		super(AntiLogoMenu, self).close(code)

	def exit(self):
		self.save()
		self.close(0)

	def stop(self):
		self.save()
		self.close(1)

	def go(self):
		selection = self["menu"].getCurrent()
		selection[1]()

	def activate(self):
		global dirty
		if dirty:
			self.exit()
		elif self.index >= 0:
			self.display.dlgs[self.index].hide()
			self.list[self.index].show()

	def deActivate(self):
		global dirty
		if dirty:
			self.exit()
		elif self.index >= 0:
			self.display.dlgs[self.index].show()
			self.list[self.index].hide()

	def add(self):
		global dirty
		if dirty:
			self.exit()
		else:
			self.deActivate()
			x = 60
			y = 30
			if FHD:
				x = 90
				y = 45
			dlgNoBorder = self.session.instantiateDialog(AntiLogoScreen, size=[x, x], position=[y, y], color=4)
			dlgWithBorder = self.session.instantiateDialog(AntiLogoScreen, size=dlgNoBorder.size, position=dlgNoBorder.position, color=dlgNoBorder.color, border=True)
			self.display.dlgs.append(dlgNoBorder)
			self.list.append(dlgWithBorder)
			self.index = len(self.list) - 1
			self.activate()

	def remove(self):
		global dirty
		if dirty:
			self.exit()
		elif self.index >= 0:
			self.session.deleteDialog(self.display.dlgs[self.index])
			self.session.deleteDialog(self.list[self.index])
			del self.display.dlgs[self.index]
			del self.list[self.index]
			if self.index > len(self.list) - 1:
				self.index -= 1
				self.activate()

	def next(self):
		global dirty
		if dirty:
			self.exit()
		elif len(self.list) > 0:
			self.deActivate()
			self.index += 1
			self.index %= len(self.list)
			self.activate()

	def save(self):
		global dirty
		if not dirty:
			if self.display.service is not None:
				for preset in list(self.display.service):
					self.display.service.remove(preset)
				for dlg in self.list:
					preset = newPreset(x=dlg.position[0], y=dlg.position[1], width=dlg.size[0], height=dlg.size[1], color=dlg.color)
					self.display.service.append(preset)

	def stepUp(self):
		if self.stepindex < len(self.steplist) - 1:
			self.stepindex += 1

	def stepDown(self):
		if self.stepindex > 0:
			self.stepindex -= 1

	def move(self):
		global dirty
		if dirty:
			self.exit()
		elif self.index >= 0:
			self.session.open(AntiLogoMove, self.display.dlgs[self.index], self.list[self.index], self.steplist[self.stepindex])

	def resize(self):
		global dirty
		if dirty:
			self.exit()
		elif self.index >= 0:
			self.session.open(AntiLogoResize, self.display.dlgs[self.index], self.list[self.index], self.steplist[self.stepindex])

	def color(self):
		global dirty
		if dirty:
			self.exit()
		elif self.index >= 0:
			self.session.openWithCallback(self.colorChanged, AntiLogoColor, self.display.dlgs, self.list, self.index)

	def colorChanged(self, newColor):
		global dirty
		if dirty:
			self.exit()
		elif newColor >= 0:
			self.display.dlgs[self.index].color = newColor
			self.list[self.index].color = newColor
			self.color()

def main(session, **kwargs):
	if session.nav.getCurrentService():
		dlg = session.open(AntiLogoMain)
		dlg.openMenu()

def autostart(reason, session=None, **kwargs):
	global services, config, configfilename
	if reason == 1:
		if services is not None:
			for service in list(services):
				if len(list(service)) == 0:
					services.remove(service)
		write(config, configfilename)

def sessionstart(reason, session=None, **kwargs):
	global display
	if reason == 0 and getEnabled(services):
		display = session.instantiateDialog(AntiLogoDisplay)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("AntiLogo"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
			PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart ),
			PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart)]
