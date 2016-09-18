import requests, os, re, argparse

VERSION = 1.0.0

parser = argparse.ArgumentParser(description='Oxide plugin updater')
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-pluginDir', help='Oxide plugin directory', required=True)
requiredNamed.add_argument('-login', help='oxidemod.org login', required=True)
requiredNamed.add_argument('-password', help='oxidemod.org password', required=True)
args = parser.parse_args()

data = {"login": args.login, "password": args.password}
plugin_dir = args.pluginDir
plugin_extensions = ['cs', 'py', 'lua']

plugins = []
not_added = []


class Plugin:
    def __init__(self, filename, name, author, version, resource_id):
        self.name = name
        self.author = author
        self.version = version
        self.resource_id = resource_id
        self.filename = filename

    def __str__(self):
        return self.name + " " + self.version + " by " + self.author + " with ResourceId: " + self.resource_id


def get_plugin_info(name, extension):
    full_name = name + "." + extension
    if extension == "cs":
        result = get_csharp_plugin_info(full_name)
    if extension == "py":
        result = get_python_plugin_info(full_name)
    if extension == "lua":
        result = get_lua_plugin_info(full_name)

    if result != "":
        not_added.append(full_name + " Reason: " + result)


def get_csharp_plugin_info(full_name):
    # [Info("BetterLoot", "Fujikura/dcode", "2.8.0", ResourceId = 828)]

    plugin_file = open(os.path.join(plugin_dir, full_name), 'r')
    plugin_code = plugin_file.read()
    info_split = plugin_code.split("[Info(")
    if len(info_split) == 2:
        raw_info_split = info_split[1].split(")]")
        if len(raw_info_split) >= 2:
            raw_info = raw_info_split[0]
            name = ""
            author = ""
            version = ""
            resource_id = ""

            info_split = raw_info.split(",")
            if len(info_split) > 0:
                name = info_split[0].lstrip().strip().replace("\"", "")
            if len(info_split) > 1:
                author = raw_info.split(",")[1].lstrip().strip().replace("\"", "")
            if len(info_split) > 2:
                version = raw_info.split(",")[2].lstrip().strip().replace("\"", "")
            if len(info_split) > 3:
                resource_id = raw_info.split(",")[3].replace("\"", "").replace("ResourceId", "").replace("=",
                                                                                                         "").lstrip().strip()
            if name != "" and resource_id != "":
                plugins.append(Plugin(full_name, name, author, version, resource_id))
                return ""
            else:
                if name == "":
                    return "Not found name"
                if resource_id == "":
                    return "Not found resource"
    return "Unknown reason"


def get_python_plugin_info(full_name):
    # self.Title = "NotePad"
    # self.Author = "OMNI-Hollow"
    # self.Version = V 0.0.2
    # self.ResourceId = 1154

    plugin_file = open(os.path.join(plugin_dir, full_name), 'r')
    name = ""
    author = ""
    version = ""
    resource_id = ""

    for line in plugin_file:
        if "=" in line:
            line = line.replace(" ", "").replace("=", "").replace("\"", "").replace("\t", "").strip()
            if "self.Title" in line:
                name = line.replace("self.Title", "").lstrip().strip()
            else:
                return "Not found name"
            if "self.Author" in line:
                author = line.replace("self.Author", "").lstrip().strip()
            if "self.Version" in line:
                version = line.replace("self.Version", "").replace("V", "").lstrip().strip()
            if "self.ResourceId" in line:
                resource_id = line.replace("self.ResourceId", "").lstrip().strip()
            else:
                return "Not found resource"
    if name != "" and resource_id != "":
        plugins.append(Plugin(full_name, name, author, version, resource_id))
        return ""
    return "Unknown reason"


def get_lua_plugin_info(full_name):
    # PLUGIN.Title = "Push API"
    # PLUGIN.Version = V(0, 2, 0)
    # PLUGIN.Description = "API for sending messages via mobile notification services."
    # PLUGIN.Author = "Wulf / Luke Spragg"
    # PLUGIN.Url = "http://oxidemod.org/plugins/705/"
    # PLUGIN.ResourceId = 705

    plugin_file = open(os.path.join(plugin_dir, full_name), 'r')
    name = ""
    author = ""
    version = ""
    resource_id = ""

    for line in plugin_file:
        if "=" in line:
            line = line.replace("=", "").replace("\"", "").replace("\t", "").replace("(", "").replace(")", "").strip()
            if "PLUGIN.Title" in line:
                name = line.replace("PLUGIN.Title", "").lstrip().strip()
            else:
                return "Not found name"
            if "PLUGIN.Author" in line:
                author = line.replace("PLUGIN.Author", "").lstrip().strip()
            if "PLUGIN.Version" in line:
                version = line.replace("PLUGIN.Version", "").replace("V", "").replace(",", ".").lstrip().strip()
            if "PLUGIN.ResourceId" in line:
                resource_id = line.replace("PLUGIN.ResourceId", "").lstrip().strip()
            else:
                return "Not found resource"
    if name != "" and resource_id != "":
        plugins.append(Plugin(full_name, name, author, version, resource_id))
        return ""
    return "Unknown reason"


def fetch_plugins():
    for filename in os.listdir(plugin_dir):
        split_filename = filename.split(".")
        if len(split_filename) == 2:
            name = split_filename[0]
            extension = split_filename[1]
            if extension in plugin_extensions and name != "plugin_updater":
                get_plugin_info(name, extension)


def login():
    login_url = "http://www.oxidemod.org/login/login"
    session = requests.session()
    session.post(login_url, data)
    return session


def download_file(s, url, filename):
    r = s.get(url, stream=True)
    with open(os.path.join(plugin_dir, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return filename


def download_plugins(session):
    for plugin in plugins:
        plugin_page = 'http://oxidemod.org/plugins/' + plugin.resource_id
        r = session.get(plugin_page)

        print("-> " + str(plugin))
        pattern = r"""plugins/.*\.""" + plugin.resource_id + """/download\?version=([0-9]*)"""
        version_id_groups = re.findall(pattern, r.text)
        if len(version_id_groups) > 0:
            version_id = version_id_groups[0]
            download_url = 'http://oxidemod.org/plugins/' + plugin.name + '.' + plugin.resource_id + "/download?version=" + version_id
            download_file(session, download_url, plugin.filename)
        else:
            not_added.append(plugin.filename + "Reason: Couldnt find download link. Page: " + plugin_page)
            download_file(session, plugin_page, plugin.filename + ".page")


def printInfo(message):
    print("############################################")
    print("#####   " + message + "")
    print("############################################")


printInfo("Oxide plugin updater " + str(VERSION) + " By W4rGo")
print("Fetching plugins...")
fetch_plugins()
print("Connecting to oxide Mod...")
session = login()
print("Downloading plugins...")
download_plugins(session)

if len(not_added) > 0:
    print("")
    print("")
    print("The following plugins didnt have well constructed headers and were not updated, update them manually:");
    for not_added_plugin in not_added:
        print("-> " + not_added_plugin)
