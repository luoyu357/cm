import os
from pprint import pprint

import cm4
import cm4.vbox
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.dotdict import dotdict
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cm4 import __version__
from cm4.vbox.provider import VboxProvider

# from cm4.mongo.MongoDBController import MongoDBController
# from cm4.mongo.MongoDBController import MongoInstaller


# pprint (vbox.vm.list())
# vbox.vm.execute("w2", "uname")
# pprint (vbox.image.list())

#
# TODO: revisit Printer

def defaults():
    """
    default values
    :return: a number of default values for memory, image, and script
    :rtype: dotdict
    """
    # TODO, read this from yaml file
    d = dotdict()
    d.memory = 1024
    # d.image = "ubuntu/xenial64"
    d.image = "ubuntu/trusty64"
    d.port = 8080
    d.script = None
    return d


#
# TODO: this seems generally useful, we may want to put this in common
#
def _convert(lst, id="name"):
    d = {}
    for entry in lst:
        d[entry[id]] = entry
    return d


# noinspection PyPep8Naming
def _LIST_PRINT(l, output, order=None):
    if output in ["yaml", "dict", "json"]:
        l_converted = _convert(l)
    else:
        l_converted = l

    result = Printer.write(l_converted,
                           order=order,
                           output=output)

    if output in ["table", "yaml", "json", "csv"]:
        print(result)
    else:
        pprint(result)


class VboxCommand(PluginCommand):

    # noinspection PyUnusedLocal
    @command
    def do_vbox(self, args, arguments):
        """
        ::

          Usage:
            vbox version [--format=FORMAT]
            vbox image list [--format=FORMAT]
            vbox image find KEYWORDS...
            vbox image add NAME
            vbox image delete NAME
            vbox vm list [--format=FORMAT] [-v]
            vbox vm delete NAME
            vbox vm config [NAME]
            vbox vm ip [NAME] [--all]
            vbox vm create [NAME] ([--memory=MEMORY] [--image=IMAGE] [--script=SCRIPT] | list)
            vbox vm boot [NAME] ([--memory=MEMORY] [--image=IMAGE] [--port=PORT] [--script=SCRIPT] | list)
            vbox vm ssh [NAME] [-e COMMAND]
        """

        arguments.format = arguments["--format"] or "table"
        arguments.verbose = arguments["-v"]
        arguments.all = arguments["--all"]

        print(arguments)

        if arguments.version:
            versions = {
                "vbox": {
                    "attribute": "Vagrant Version",
                    "version": cm4.vbox.version(),
                },
                "cloudmesh-vbox": {
                    "attribute": "cloudmesh vbox Version",
                    "version": __version__
                }
            }
            _LIST_PRINT(versions, arguments.format)

        elif arguments.image and arguments.list:
            l = VboxProvider.list_images()

            _LIST_PRINT(l, arguments.format, order=["name", "provider", "date"])

        elif arguments.image and arguments.add:
            try:
                l = VboxProvider.add_image(arguments.NAME)
                print(l)
            except Exception as e:
                print(e)
            return ""

        elif arguments.image and arguments.delete:
            try:
                l = VboxProvider.delete_image(arguments.NAME)
                print(l)
            except Exception as e:
                print(e)
            return ""


        elif arguments.image and arguments.find_image:

            VboxProvider.find_image(arguments.KEYWORDS)
            return ""

        elif arguments.vm and arguments.list:

            l = VboxProvider().nodes()
            _LIST_PRINT(l,
                        arguments.format,
                        order=["name", "state", "id", "provider", "directory"])
            return ""

        elif arguments.create and arguments.list:

            result = Shell.cat("{NAME}/Vagrantfile".format(**arguments))
            if result is not None:
                print(result)
            return ""

        elif arguments.create:

            d = defaults()

            arguments.memory = arguments["--memory"] or d.memory
            arguments.image = arguments["--image"] or d.image
            arguments.script = arguments["--script"] or d.script

            server = VboxProvider()
            server.create(
                name=arguments.NAME,
                memory=arguments.memory,
                image=arguments.image,
                script=arguments.script)

        elif arguments.config:

            # arguments.NAME
            d = VboxProvider().info(name=arguments.NAME)

            result = Printer.attribute(d, output=arguments.format)

            print(result)

        elif arguments.ip:

            data = []
            result = VboxProvider().execute(arguments.NAME, "ifconfig")
            if result is not None:
                lines = result.splitlines()[:-1]
                for line in lines:
                    if "inet addr" in line:
                        line = line.replace("inet addr", "ip")
                        line = ' '.join(line.split())
                        _adresses = line.split(" ")
                        address = {}
                        for element in _adresses:
                            attribute, value = element.split(":")
                            address[attribute] = value
                        data.append(address)
            if arguments.all:
                d = {}
                i = 0
                for e in data:
                    d[str(i)] = e
                    i = i + 1
                result = Printer.attribute(d, output=arguments.format)
                print(result)
            else:
                for element in data:
                    ip = element['ip']
                    if ip == "127.0.0.1" or ip.startswith("10."):
                        pass
                    else:
                        print(element['ip'])


        elif arguments.boot:

            d = defaults()

            arguments.memory = arguments["--memory"] or d.memory
            arguments.image = arguments["--image"] or d.image
            arguments.script = arguments["--script"] or d.script
            arguments.port = arguments["--port"] or d.port

            node = VboxProvider().boot(
                name=arguments.NAME,
                memory=arguments.memory,
                image=arguments.image,
                script=arguments.script,
                port=arguments.port)

        elif arguments.delete:

            result = VboxProvider().delete(name=arguments.NAME)
            print(result)

        elif arguments.ssh:

            if arguments.COMMAND is None:
                os.system("cd {NAME}; vbox ssh {NAME}".format(**arguments))
            else:
                result = VboxProvider().execute(arguments.NAME, arguments.COMMAND)
                if result is not None:
                    lines = result.splitlines()[:-1]
                    for line in lines:
                        print(line)

        else:

            print("use help")

        result = ""
        return result
